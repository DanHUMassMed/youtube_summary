import os
import uuid
import time
from datetime import datetime
import ollama
import markdown2
from weasyprint import HTML
import mdformat
from app.youtube_transcribe import extract_video_id, get_transcript, get_video_title, get_video_thumbnail, chunk_text
from app import prompts
from app.ollama_utils import OllamaUtils
from app.checkpoint import set_checkpoint_directory, checkpoint

class LexPodcastSummary:
    def __init__(self, podcast_url, *, results_dir = None):
        
        self.lex_url = podcast_url
        self.thumbnail_url = None
        self._title = None

        self.api_key = os.getenv("YOUTUBE_SEARCH_API")
        if self.api_key is None:
            raise EnvironmentError("YOUTUBE_SEARCH_API environment variable not set")

        if results_dir is None:
            video_id = extract_video_id(podcast_url)
            video_title = get_video_title(video_id, self.api_key)
            self.unique_title = self._create_unique_title(video_title)
            self.results_dir = self._create_results_dir(self.unique_title)
        else:
            self.results_dir = results_dir
            
        set_checkpoint_directory(self.results_dir)
        
        self.transcript_file_path = f"{self.results_dir}/transcript.txt"
        self.thumbnail_file_path = f"{self.results_dir}/thumbnail.jpg"
                
        self.model_name = 'llama3.3:latest'
        self.temperature = 0.0
        self.num_cxt = 32*1024
        self.raw_text_chunk_size = 32*1024
        self.text_chunk_overlay_size = 100
                        
    
    @property
    def title(self):
        """Getter for the title property."""
        if self._title is None:
            title_path = os.path.join(self.results_dir, 'title.txt')
            if os.path.exists(title_path):
                with open(title_path, 'r') as file:
                    self._title = file.read().strip()
        return self._title

    @title.setter
    def title(self, value):
        """Setter for the title property."""
        title_path = os.path.join(self.results_dir, 'title.txt')
        with open(title_path, 'w') as file:
            file.write(value)
        self._title = value
            
                 
    def _create_unique_title(self, video_title):
        random_uuid = uuid.uuid4()
        uuid_int = random_uuid.int
        five_digit_number = 10000 + (uuid_int % 90000)

        words = video_title.split()[:2]
        first_two_words = ' '.join(words)
        
        remove_chars = '",<>:;|='
        trans_table = str.maketrans('', '', remove_chars)
        cleaned_text = first_two_words.translate(trans_table)
        cleaned_text = cleaned_text.replace(' ','_')
        
        return f"{cleaned_text}-{five_digit_number}"


    def _create_results_dir(self, results_dir):
        """ Create the directory to maintain results """
        results_dir = f"podcast_{results_dir.lower()}"
        dir_path = os.path.join(os.getcwd(), results_dir)        
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return results_dir
            
    def _elapsed_time(self, start_time, end_time = None):
        """ Used for logging to time function calls. """
        if end_time is None:
            end_time = time.perf_counter()
        elapsed_time_seconds = end_time - start_time
        minutes, seconds = divmod(elapsed_time_seconds, 60)
        formatted_time = f"{int(minutes)} minutes and {int(seconds)} seconds"
        return formatted_time


    @checkpoint     
    def _get_title_and_transcript(self):
        """ Pulls the details of the video from youtube. 
        This includes the video title, transcript text and a thumbnail."""
        video_id = extract_video_id(self.lex_url)
        self.title = get_video_title(video_id, self.api_key)
        self.thumbnail_url = get_video_thumbnail(video_id, self.api_key, self.thumbnail_file_path)
        transcript = get_transcript(video_id, self.transcript_file_path)
        return (self.title, transcript)
    
    def _chunk_transcript(self):
        """Simplifies the call to chunk_text because we already know all the parameters"""
        return chunk_text(self.transcript_file_path, self.raw_text_chunk_size, self.text_chunk_overlay_size)

    
    def _summarize_chunks(self, chunks, max_summary_response_size):
        """ Summarize each chunk of the transcript individually 
        NOTE: OLLAMA_NUM_PARALLEL=3 does work if you map multiple processes but it does not save time."""
        for index, chunk in enumerate(chunks):
            print(f"Starting to process chunk {index +1}")
            self._summarize_chunk(chunk, max_summary_response_size, index +1)

    @checkpoint
    def _summarize_chunk(self, context: str, max_summary_response_size: int, chunk_index: int) -> str:
        start_time = time.perf_counter()
        summarize_chunk_prompt = prompts.SUMMARIZE_CHUNK_PROMPT.format(max_summary_response_size=max_summary_response_size)
        
        ollama_response = ollama.generate(
            model = self.model_name, 
            prompt = f"== Title ==: {self.title}\n== Context ==\n{context}\n\n{summarize_chunk_prompt}",
            system = prompts.MAIN_SYSTEM_PROMPT,
            options = {'temperature':self.temperature, 'num_ctx':self.num_cxt}
            )
        
        if ollama_response.get('response') is not None:
            self._save_summarize_chunk_context(ollama_response['response'], chunk_index)
        else:
            print("THIS IS A PROBLEM: No Response generated for Chunk {chunk_index}.")
            
        formatted_time = self._elapsed_time(start_time)
        print(f"Total time for summarize_chunk of chunk {chunk_index} {formatted_time}.")
        return ollama_response

    def _save_summarize_chunk_context(self, content, chunk_index):
        unique_id = uuid.uuid4()
        filename = f"{self.results_dir}/chunk_results_{chunk_index}_{unique_id}.txt"
        
        with open(filename, 'w') as file:
            file.write(str(content))
    
    def _read_and_concatenate_summaries(self):
        full_content = ""
        if self.title:
            title_header = f"== TITLE ==\n"
            full_content += title_header
            full_content += self.title + "\n"
            
        files = os.listdir(self.results_dir)
        
        # Filter files that start with 'chunk_results_' and end with '.txt'
        chunk_files = [f for f in files if f.startswith('chunk_results_') and f.endswith('.txt')]
        
        # Sort the files based on the numeric part after 'chunk_results_'
        chunk_files.sort(key=lambda x: int(x.split('_')[2].split('.')[0]))
        
        # Iterate over each sorted chunk file
        for index, filename in enumerate(chunk_files, start=1):
            file_path = os.path.join(self.results_dir, filename)
            with open(file_path, 'r') as file:
                # Read the content of the file
                content = file.read()
            
            # Create a header for the subcontext
            subcontext_header = f"== SubContext {index+1} ==\n"
            
            # Append the header and content to the full_content string
            full_content += subcontext_header + content + "\n"
        
        return full_content
    
    @checkpoint
    def _main_body_text(self, concatenated_content):
        # Generate a response using the 'llama3.2' model
        prompt = prompts.CREATE_REPORT_BODY_PROMPT
        system_prompt = prompts.REPORT_SECTION_SYSTEM_PROMPT
        
        ollama_response = ollama.generate(
            model = self.model_name,
            prompt=f"{concatenated_content}\n{prompt}",
            system=system_prompt,
            options={'temperature':self.temperature,'num_ctx':self.num_cxt}
        )
        main_body_text = ollama_response.get('response')
        file_path = f"{self.results_dir}/main_body.txt"
        with open(file_path, 'w') as file:
            file.write(main_body_text)
        return main_body_text

    @checkpoint 
    def _introduction_text(self, concatenated_content):
        # Generate a response using the 'llama3.2' model
        prompt = prompts.CREATE_INTRODUCTION_PROMPT
        system_prompt = prompts.REPORT_SECTION_SYSTEM_PROMPT
        
        ollama_response = ollama.generate(
            model = self.model_name,
            prompt=f"{concatenated_content}\n{prompt}",
            system=system_prompt,
            options={'temperature':self.temperature,'num_ctx':self.num_cxt}
        )
        main_body_text = ollama_response.get('response')
        file_path = f"{self.results_dir}/introduction.txt"
        with open(file_path, 'w') as file:
            file.write(main_body_text)
        return main_body_text

    @checkpoint 
    def _conclusion_text(self, concatenated_content):
        # Generate a response using the 'llama3.2' model
        prompt = prompts.CREATE_CONCLUSION_PROMPT
        system_prompt = prompts.REPORT_SECTION_SYSTEM_PROMPT
        
        ollama_response = ollama.generate(
            model = self.model_name,
            prompt=f"{concatenated_content}\n{prompt}",
            system=system_prompt,
            options={'temperature':self.temperature,'num_ctx':self.num_cxt}
        )
        main_body_text = ollama_response.get('response')
        file_path = f"{self.results_dir}/conclusion.txt"
        with open(file_path, 'w') as file:
            file.write(main_body_text)
        return main_body_text

    @checkpoint
    def _final_report_text(self, concatenated_content):
        # Generate a response using the 'llama3.2' model
        prompt = prompts.CREATE_FINAL_REPORT_PROMPT
        system_prompt = prompts.FINAL_REPORT_SYSTEM_PROMPT
        
        ollama_response = ollama.generate(
            model = self.model_name,
            prompt=f"{concatenated_content}\n{prompt}",
            system=system_prompt,
            options={'temperature':self.temperature,'num_ctx':self.num_cxt}
        )
        main_body_text = ollama_response.get('response')
        file_path = f"{self.results_dir}/final_report.txt"
        with open(file_path, 'w') as file:
            file.write(main_body_text)
        return main_body_text

    def _load_text(self, file_name):
        file_path = f"{self.results_dir}/{file_name}"
        with open(file_path, 'r', encoding='utf-8') as file:
            file_text = file.read()
        return file_text

    def _markdown_to_pdf(self, markdown_content):
        markdown_content = mdformat.text(markdown_content, extensions={"gfm"})

        thumbnail = f"![Thumbnail](file://{os.path.abspath(self.thumbnail_file_path)})\n\n"
        markdown_content = thumbnail + f"[{self.lex_url}]({self.lex_url})\n\n" + markdown_content
        
        output_pdf_path = f"{self.results_dir}/{self.unique_title}.pdf"
        html_content = markdown2.markdown(markdown_content)
        HTML(string=html_content).write_pdf(output_pdf_path)


    ###############################################################3
    # Putting it all together
    
    def config(self,
                model_name = None, 
                temperature = None,
                num_cxt = None,
                raw_text_chunk_size = None,
                text_chunk_overlay_size = None):
        
        ollama_utils = OllamaUtils()

        if model_name is not None:
            if ollama_utils.model_exists(model_name):
                self.model_name = model_name
            else:
                raise KeyError(f"Model {model_name} does not exists")
            
        if temperature is not None:
            self.temperature = temperature
            
        # Define the Context Window Size for the Model
        if num_cxt is not None:
            max_num_ctx = ollama_utils.model_context_size(model_name)
            if num_cxt <= max_num_ctx:
                self.num_cxt = num_cxt # Tokens (Note a token is ~4 Bytes)
            else:
                raise Exception("ERROR: num-ctx provided is larger than max_num_ctx ")
            
        # Chunk the raw transcript text into xxk (32k) Byte Chunks for processing as 
        # if the full text is to large the Context Window size
        if raw_text_chunk_size is not None:
            self.raw_text_chunk_size = raw_text_chunk_size
            
        # Overlap the end of each chunk in case we cutoff a sentence we 
        # want to have its meaning maintained in the next chunk 
        if text_chunk_overlay_size is not None:
            self.text_chunk_overlay_size = text_chunk_overlay_size

    def create_summary_report(self):
        total_time_start = time.perf_counter()
        self._get_title_and_transcript()
        chunks = self._chunk_transcript()
        print(f"We have {len(chunks)} chunks.")
        print(f"We are use {self.model_name}.")
        
        # We do not want to exceed to context window when we add all the summary chunks together
        # Rational: We know the context window is made of tokens each token is approximately 4 bytes
        # We can be very conservative and only use 1/2 the context for the summary text
        # The rest can be for detailed prompts
        
        max_summary_response_size = ((self.num_cxt * 4)*0.6)/len(chunks)
        print(f"Max Response size {max_summary_response_size}")
        
        start_time = time.perf_counter()
        self._summarize_chunks(chunks, max_summary_response_size)
        
        formatted_time = self._elapsed_time(start_time)
        print(f"Total time to summarize chunk(s) took {formatted_time}.")
        
        concatenated_content = self._read_and_concatenate_summaries()

        start_time = time.perf_counter()
        introduction_text = self._introduction_text(concatenated_content)
        introduction_text = introduction_text if introduction_text else self._load_text('introduction.txt')
        formatted_time = self._elapsed_time(start_time)
        print(f"Total time write the introduction took {formatted_time}.")

        start_time = time.perf_counter()
        main_body_text = self._main_body_text(concatenated_content)
        main_body_text = main_body_text if main_body_text else self._load_text('main_body.txt')
        formatted_time = self._elapsed_time(start_time)
        print(f"Total time to write the main body took {formatted_time}.")

        start_time = time.perf_counter()
        conclusion_text = self._conclusion_text(concatenated_content)
        conclusion_text = conclusion_text if conclusion_text else self._load_text('conclusion.txt')
        formatted_time = self._elapsed_time(start_time)
        print(f"Total time to write the conclusion took {formatted_time}.")
        
        draft_report = (
            "== TITLE == \n"
            f"{self.title} \n\n"
            "== INTRODUCTION == \n"
            f"{introduction_text} \n\n"
            "== REPORT BODY == \n"
            f"{main_body_text} \n\n"
            "== CONCLUSION == \n"
            f"{conclusion_text}"
        )
        start_time = time.perf_counter()
        final_report_text = self._final_report_text(draft_report)
        final_report_text = final_report_text if final_report_text else self._load_text('final_report.txt')
        formatted_time = self._elapsed_time(start_time)
        print(f"Total time to write finalize the report took {formatted_time}.")

        print("--"*40)
        #print(final_report_text)
        self._markdown_to_pdf(final_report_text)
        
        formatted_time = self._elapsed_time(total_time_start)
        print("="*60)
        print(f"Total time to execute took {formatted_time}.")
    