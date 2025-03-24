import json
import os
from functools import wraps

# Global variable to store the checkpoint directory
CHECKPOINT_DIRECTORY = None
CHECKPOINT_CALL_COUNTER = 0

def set_checkpoint_directory(directory):
    """Set the global directory for storing checkpoints."""
    global CHECKPOINT_DIRECTORY
    CHECKPOINT_DIRECTORY = directory
    # Ensure the directory exists
    if CHECKPOINT_DIRECTORY:
        os.makedirs(CHECKPOINT_DIRECTORY, exist_ok=True)

def reset_checkpoint_counter():
    """Reset the checkpoint counter."""
    global CHECKPOINT_CALL_COUNTER
    CHECKPOINT_CALL_COUNTER = 0

# Helper function to get the filepath for the checkpoint JSON file
def get_checkpoint_filepath():
    """Get the path to the checkpoint file based on the configured or default directory."""
    if CHECKPOINT_DIRECTORY:
        return os.path.join(CHECKPOINT_DIRECTORY, 'checkpoints.json')
    return 'checkpoints.json'  # Default location in the current directory

# Helper function to load checkpoints from the checkpoint JSON file
def load_checkpoints():
    """Load the checkpoint data from a JSON file."""
    filepath = get_checkpoint_filepath()
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

# Helper function to save checkpoints to the checkpoint JSON file
def save_checkpoints(checkpoints):
    """Save the checkpoint data to a JSON file."""
    filepath = get_checkpoint_filepath()
    with open(filepath, 'w') as f:
        json.dump(checkpoints, f, indent=4)

# The checkpoint decorator (uses the function name as the checkpoint name)
def checkpoint(func):
    """Decorator that checks for the existence of a checkpoint before executing the function.
    
    The checkpoint name is automatically set to the name of the decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Use the function's name as the checkpoint name
        global CHECKPOINT_CALL_COUNTER
        CHECKPOINT_CALL_COUNTER += 1
        checkpoint_name = f"{func.__name__}-{CHECKPOINT_CALL_COUNTER}"
        
        # Load existing checkpoints
        checkpoints = load_checkpoints()
        
        # Check if the checkpoint already exists
        if checkpoint_name in checkpoints:
            print(f"Skipping '{checkpoint_name}' as checkpoint already exists.")
            return None  # Skip execution if checkpoint exists
        
        try:
            # Execute the function if checkpoint does not exist
            result = func(*args, **kwargs)
            
            # If no exception, add the checkpoint and save
            args_str = json.dumps([str(arg) for arg in args]).replace('"','')
            kwargs_str = json.dumps({k: str(v) for k, v in kwargs.items()}).replace('"','')
            checkpoints[checkpoint_name] = {'args_str':args_str,'kwargs_str':kwargs_str}
            save_checkpoints(checkpoints)
            
            return result  # Return the function result
        except Exception as e:
            print(f"Error during '{checkpoint_name}': {str(e)}")
            raise e  # Re-raise the exception to be handled elsewhere

    return wrapper