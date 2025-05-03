import os
import logging
import asyncio
import uuid
import traceback
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

# Check if Daytona SDK is available
try:
    from daytona_sdk import Daytona, DaytonaConfig
    DAYTONA_AVAILABLE = True
except ImportError:
    DAYTONA_AVAILABLE = False

class CodeExecutor:
    """Execute code in a secure sandbox environment."""
    
    def __init__(self, config=None):
        """
        Initialize the code executor.
        
        Args:
            config (dict, optional): Configuration for code execution
        """
        self.config = config or {}
        self.daytona_api_key = self.config.get("daytona_api_key", os.environ.get("DAYTONA_API_KEY", ""))
        self.default_timeout = self.config.get("sandbox_timeout", 30)
        self.default_memory_limit = self.config.get("sandbox_memory_limit", "2Gi")
        self.default_cpu_limit = self.config.get("sandbox_cpu_limit", "2000m")
        
        # Check if Daytona is available
        if not DAYTONA_AVAILABLE:
            logger.warning("Daytona SDK not available. Please install with: pip install daytona-sdk")
        elif not self.daytona_api_key:
            logger.warning("Daytona API key not found in configuration or environment variables")
        else:
            try:
                self.daytona_client = DaytonaConfig(api_key=self.daytona_api_key)
                logger.info("Daytona client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Daytona client: {str(e)}")
                self.daytona_client = None
    
    async def execute_code(self, code: str, language: str = "python", timeout: int = None) -> Dict[str, Any]:
        """
        Execute code in a Daytona sandbox environment.
        
        Args:
            code (str): The code to execute
            language (str, optional): The programming language (python, javascript, bash)
            timeout (int, optional): Execution timeout in seconds
            
        Returns:
            Dict[str, Any]: The execution result
        """
        if not DAYTONA_AVAILABLE:
            return {
                "success": False,
                "error": "Daytona SDK not available. Please install with: pip install daytona-sdk"
            }
            
        if not self.daytona_client:
            return {
                "success": False,
                "error": "Daytona client not initialized. Please check API key."
            }
            
        # Set timeout
        timeout = timeout or self.default_timeout
        
        # Generate a unique sandbox ID
        sandbox_id = f"ai-agent-{uuid.uuid4().hex[:8]}"
        process = None
        
        try:
            # Configure sandbox
            sandbox_config = {
                "id": sandbox_id,
                "language": language.lower(),
                "image": self._get_secure_image(language),
                "entrypoint": ["/bin/sh", "-c"],
                "resources": {
                    "cpu": self.default_cpu_limit,
                    "memory": self.default_memory_limit,
                    "ephemeral-storage": "1Gi"
                }
            }

            # Create sandbox with timeout
            sandbox = await asyncio.wait_for(
                self.daytona_client.create_sandbox(sandbox_config),
                timeout=10
            )
            logger.info(f"Created sandbox: {sandbox_id}")

            try:
                # Set up workspace
                workspace = f"/tmp/workspace-{uuid.uuid4().hex[:8]}"
                await sandbox.filesystem.mkdir(workspace)
                
                # Prepare code file
                file_config = self._get_language_config(language)
                code_file = os.path.join(workspace, f"main{file_config['ext']}")
                
                # Write code
                await sandbox.filesystem.write(
                    code_file,
                    code,
                    mode=0o755  # Executable permissions
                )

                # Execute code
                process = await sandbox.process.start(
                    command=file_config['cmd'].format(file=code_file),
                    working_dir=workspace,
                    limits={
                        "cpu": self.default_cpu_limit,
                        "memory": self.default_memory_limit,
                        "timeout": timeout,
                        "processes": 20,
                        "file_size": "100Mi"
                    },
                    env={
                        "PYTHONPATH": workspace,
                        "PYTHONUNBUFFERED": "1",
                        "PATH": "/usr/local/bin:/usr/bin:/bin"
                    }
                )

                # Stream output
                stdout_buffer = []
                stderr_buffer = []
                
                async for output in process.stream():
                    if len('\n'.join(stdout_buffer)) > 5_000_000:  # 5MB output limit
                        raise Exception("Output size limit exceeded")
                        
                    if output.type == "stdout":
                        stdout_buffer.append(output.data)
                    elif output.type == "stderr":
                        stderr_buffer.append(output.data)

                exit_code = await asyncio.wait_for(process.wait(), timeout=timeout)

                metrics = await process.metrics()
                
                return {
                    "success": exit_code == 0,
                    "stdout": "\n".join(stdout_buffer),
                    "stderr": "\n".join(stderr_buffer),
                    "exit_code": exit_code,
                    "language": language,
                    "metrics": {
                        "cpu_usage": metrics.get("cpu", "N/A"),
                        "memory_usage": metrics.get("memory", "N/A"),
                        "execution_time": metrics.get("duration", "N/A")
                    }
                }

            except asyncio.TimeoutError:
                logger.warning(f"Code execution timed out: {sandbox_id}")
                if process:
                    await process.terminate()
                return {
                    "success": False,
                    "error": f"Execution timed out after {timeout} seconds"
                }
                
            finally:
                await self._cleanup_sandbox(sandbox_id)

        except Exception as e:
            logger.error(f"Sandbox error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _cleanup_sandbox(self, sandbox_id: str) -> None:
        """Clean up the sandbox after execution."""
        try:
            await self.daytona_client.delete_sandbox(sandbox_id)
            logger.info(f"Cleaned up sandbox: {sandbox_id}")
        except Exception as e:
            logger.error(f"Error cleaning up sandbox {sandbox_id}: {str(e)}")
    
    def _get_secure_image(self, language: str) -> str:
        """Get the appropriate secure container image for the language."""
        images = {
            "python": "daytona/python-secure:3.9-slim",
            "javascript": "daytona/node-secure:16-slim",
            "bash": "daytona/bash-secure:5.1-slim"
        }
        return images.get(language.lower(), images["python"])
    
    def _get_language_config(self, language: str) -> Dict[str, str]:
        """Get language-specific configuration."""
        configs = {
            "python": {
                "ext": ".py",
                "cmd": "python3 -u {file}"
            },
            "javascript": {
                "ext": ".js",
                "cmd": "node {file}"
            },
            "bash": {
                "ext": ".sh",
                "cmd": "bash {file}"
            }
        }
        return configs.get(language.lower(), configs["python"])