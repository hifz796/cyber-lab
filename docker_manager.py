"""
Docker Manager - Container Orchestration for Challenges
"""

import docker
import random
import secrets
from datetime import datetime, timedelta

class DockerManager:
    """Manage Docker containers for cybersecurity challenges"""
    
    def __init__(self):
        self.available = False
        self.client = None
        self.mock_mode = True
        
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            self.available = True
            self.mock_mode = False
            print("✅ Docker connection established")
        except Exception as e:
            print(f"⚠️  Docker not available: {e}")
            print("   Running in MOCK MODE - containers will be simulated")
    
    def start_container(self, user_id, challenge_id, image_name):
        """Start a Docker container for a challenge"""
        
        if self.mock_mode:
            return self._mock_start_container(user_id, challenge_id, image_name)
        
        try:
            # Generate unique container name
            container_name = f"cyberlab_user{user_id}_chal{challenge_id}_{secrets.token_hex(4)}"
            
            # Random port between 30000-40000
            host_port = random.randint(30000, 40000)
            
            # Start container
            container = self.client.containers.run(
                image_name,
                name=container_name,
                detach=True,
                remove=True,  # Auto-remove when stopped
                ports={'80/tcp': host_port},  # Map container port 80 to random host port
                mem_limit='256m',  # Memory limit
                cpu_quota=50000,  # CPU limit (50%)
                network_mode='bridge'
            )
            
            # Get container info
            container.reload()
            
            return {
                'success': True,
                'container_id': container.id,
                'container_name': container_name,
                'host': 'localhost',
                'port': host_port,
                'url': f'http://localhost:{host_port}',
                'expires_at': (datetime.now() + timedelta(hours=2)).isoformat()
            }
            
        except docker.errors.ImageNotFound:
            return {
                'error': f'Docker image "{image_name}" not found. Please build or pull the image first.',
                'suggestion': f'Try: docker pull {image_name}'
            }
        except docker.errors.APIError as e:
            return {
                'error': f'Docker API error: {str(e)}',
                'suggestion': 'Check if Docker daemon is running and accessible'
            }
        except Exception as e:
            return {
                'error': f'Failed to start container: {str(e)}'
            }
    
    def stop_container(self, user_id, challenge_id):
        """Stop a container for a specific user and challenge"""
        
        if self.mock_mode:
            return self._mock_stop_container(user_id, challenge_id)
        
        try:
            # Find containers matching the pattern
            containers = self.client.containers.list(
                filters={'name': f'cyberlab_user{user_id}_chal{challenge_id}'}
            )
            
            if not containers:
                return {'error': 'No active container found'}
            
            # Stop all matching containers
            for container in containers:
                container.stop(timeout=5)
                container.remove(force=True)
            
            return {
                'success': True,
                'message': f'Stopped {len(containers)} container(s)'
            }
            
        except Exception as e:
            return {
                'error': f'Failed to stop container: {str(e)}'
            }
    
    def stop_container_by_id(self, container_id):
        """Stop a specific container by ID (admin function)"""
        
        if self.mock_mode:
            return {'success': True, 'message': 'Mock container stopped'}
        
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=5)
            container.remove(force=True)
            
            return {
                'success': True,
                'message': 'Container stopped successfully'
            }
            
        except docker.errors.NotFound:
            return {'error': 'Container not found'}
        except Exception as e:
            return {'error': f'Failed to stop container: {str(e)}'}
    
    def get_container_status(self, user_id, challenge_id):
        """Get status of a container"""
        
        if self.mock_mode:
            return {'status': 'mock', 'running': False}
        
        try:
            containers = self.client.containers.list(
                filters={'name': f'cyberlab_user{user_id}_chal{challenge_id}'}
            )
            
            if not containers:
                return {'running': False}
            
            container = containers[0]
            return {
                'running': True,
                'container_id': container.id,
                'status': container.status,
                'ports': container.ports
            }
            
        except Exception as e:
            return {'error': str(e), 'running': False}
    
    def cleanup_expired_containers(self):
        """Cleanup containers that have been running too long"""
        
        if self.mock_mode:
            return {'cleaned': 0}
        
        try:
            # Get all cyberlab containers
            containers = self.client.containers.list(
                filters={'name': 'cyberlab_'}
            )
            
            cleaned = 0
            for container in containers:
                # Check container age (stop if > 2 hours)
                started = datetime.fromisoformat(
                    container.attrs['State']['StartedAt'].replace('Z', '+00:00')
                )
                age = datetime.now(started.tzinfo) - started
                
                if age > timedelta(hours=2):
                    container.stop(timeout=5)
                    container.remove(force=True)
                    cleaned += 1
            
            return {
                'success': True,
                'cleaned': cleaned,
                'message': f'Cleaned up {cleaned} expired containers'
            }
            
        except Exception as e:
            return {'error': f'Cleanup failed: {str(e)}'}
    
    def list_active_containers(self):
        """List all active cyberlab containers"""
        
        if self.mock_mode:
            return []
        
        try:
            containers = self.client.containers.list(
                filters={'name': 'cyberlab_'}
            )
            
            container_list = []
            for container in containers:
                container_list.append({
                    'id': container.id,
                    'name': container.name,
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'started': container.attrs['State']['StartedAt'],
                    'ports': container.ports
                })
            
            return container_list
            
        except Exception as e:
            print(f"Error listing containers: {e}")
            return []
    
    def build_challenge_image(self, dockerfile_path, image_name):
        """Build a Docker image from Dockerfile (for creating new challenges)"""
        
        if self.mock_mode:
            return {'success': True, 'message': f'Mock: Would build {image_name}'}
        
        try:
            image, build_logs = self.client.images.build(
                path=dockerfile_path,
                tag=image_name,
                rm=True  # Remove intermediate containers
            )
            
            # Collect build logs
            logs = []
            for chunk in build_logs:
                if 'stream' in chunk:
                    logs.append(chunk['stream'].strip())
            
            return {
                'success': True,
                'image_id': image.id,
                'logs': logs,
                'message': f'Successfully built {image_name}'
            }
            
        except docker.errors.BuildError as e:
            return {
                'error': 'Build failed',
                'logs': [str(log) for log in e.build_log]
            }
        except Exception as e:
            return {'error': f'Build error: {str(e)}'}
    
    # ==================== MOCK MODE FUNCTIONS ====================
    
    def _mock_start_container(self, user_id, challenge_id, image_name):
        """Mock container start for testing without Docker"""
        container_id = secrets.token_hex(32)
        port = random.randint(30000, 40000)
        
        return {
            'success': True,
            'container_id': container_id,
            'container_name': f'mock_container_{user_id}_{challenge_id}',
            'host': 'localhost',
            'port': port,
            'url': f'http://localhost:{port}',
            'expires_at': (datetime.now() + timedelta(hours=2)).isoformat(),
            'mock': True,
            'note': 'This is a simulated container. Set up Docker for real containers.'
        }
    
    def _mock_stop_container(self, user_id, challenge_id):
        """Mock container stop"""
        return {
            'success': True,
            'message': 'Mock container stopped',
            'mock': True
        }


# Example usage and testing
if __name__ == '__main__':
    print("Testing Docker Manager...")
    
    manager = DockerManager()
    
    print("\n" + "="*60)
    print(f"Docker Available: {manager.available}")
    print(f"Mock Mode: {manager.mock_mode}")
    print("="*60)
    
    # Test starting a container
    print("\nTesting container start...")
    result = manager.start_container(user_id=1, challenge_id=1, image_name='nginx:alpine')
    print(f"Result: {result}")
    
    if result.get('success'):
        print("\nTesting container stop...")
        stop_result = manager.stop_container(user_id=1, challenge_id=1)
        print(f"Stop Result: {stop_result}")
    
    print("\n" + "="*60)