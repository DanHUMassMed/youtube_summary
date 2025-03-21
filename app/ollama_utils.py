import ollama

class OllamaUtils:
    def __init__(self):
        try:
            self.client = ollama.Client()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Ollama client: {e}")
        
        try:
            models = self.client.list()
            if 'models' in models:
                self.model_names = sorted([model['model'] for model in models['models']])
                #self.model_names = [model.replace(':latest', '') for model in model_names]
            else:
                raise ValueError("Response from the client does not contain 'models' key.")
                    
        except Exception as e:
            raise RuntimeError(f"Error while fetching or processing model list: {e}")
        
    def model_exists(self, model_name) -> bool:
        """ Does this model exist in the model list?"""
        if model_name in self.model_names:
            return True
        return False
        
    def model_context_size(self, model_name) -> int:
        """ Get the Model Context Window Size"""
        # The gemma3 model is miss defined by ollama as having only an 8k context
        if model_name=='gemma3:27b':
            return 128*1024
        try:
            details_for_model_name = self.client.show(model_name)
            if 'modelinfo' not in details_for_model_name:
                return -1

            for key, value in details_for_model_name['modelinfo'].items():
                if 'context_length' in key:
                    return value
            return -1
        except Exception as e:
            return -1
                    
    def model_base_model(self, model_name) -> int:
        """ Get the Base model for the given model name"""
        try:
            details_for_model_name = self.client.show(model_name)
            if 'modelinfo' not in details_for_model_name:
                return -1

            for key, value in details_for_model_name['modelinfo'].items():
                if 'context_length' in key:
                    return key[:-15]
            return -1
        except Exception as e:
            return -1

                       