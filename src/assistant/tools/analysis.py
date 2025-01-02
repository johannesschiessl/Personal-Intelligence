import docker
import tempfile
from pathlib import Path
from typing import Dict, Any

class Analysis:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "python:3.12-slim"
        self._ensure_image()
    
    def _ensure_image(self) -> None:
        """Ensure the Python Docker image is available locally."""
        try:
            self.client.images.get(self.image_name)
        except docker.errors.ImageNotFound:
            print(f"Pulling {self.image_name} image...")
            self.client.images.pull(self.image_name)
    
    def process(self, code: str) -> Dict[str, Any]:
        """Execute Python code safely in a Docker container.
        
        Args:
            code: The Python code to execute
            
        Returns:
            Dict containing execution results with keys:
            - success: bool indicating if execution was successful
            - output: stdout/stderr from the code execution
            - error: error message if execution failed
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "code.py"
            code_file.write_text(code)
            
            try:
                container = self.client.containers.run(
                    self.image_name,
                    command=["python", "/code/code.py"],
                    volumes={
                        temp_dir: {
                            "bind": "/code",
                            "mode": "ro"
                        }
                    },
                    mem_limit="512m",
                    memswap_limit="512m",
                    cpu_period=100000,
                    cpu_quota=50000,
                    network_mode="none",
                    remove=True,
                    detach=True 
                )
                
                try:
                    container.wait(timeout=10)
                    output = container.logs().decode('utf-8')
                    return {
                        "success": True,
                        "output": output,
                        "error": None
                    }
                    
                except Exception as e:
                    try:
                        container.kill()
                    except:
                        pass
                    return {
                        "success": False,
                        "output": None,
                        "error": f"Execution error: {str(e)}"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "output": None,
                    "error": f"Container error: {str(e)}"
                }
    