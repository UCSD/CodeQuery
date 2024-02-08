# Standard and third-party libraries
import os
import subprocess
import sys
import logging
import tempfile
from openai import OpenAI
from dotenv import load_dotenv

# Setup basic logging configuration
log_file_path = os.path.join(tempfile.gettempdir(), 'codequery.log')
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Load environment variables from .env file
load_dotenv()

def codequery(query, *paths):
	# Available models (uncomment the desired one)
	model = "gpt-4-0125-preview" # latest, context window 128k tokens
	# model = "gpt-4-turbo-preview" # context window 128k tokens
	# model = "gpt-4-1106-preview" # context window 128k tokens
	# model = "gpt-3.5-turbo-1106" # context window 16k tokens

	# Use current directory if no paths are provided
	if not paths:
		paths = ["."]

	codecontext_responses = []
	total_characters = 0
	
	for path in paths:
		# Construct the command with the path parameter before the accept parameter
		command = ['codecontext', '--path', path, '--accept', 'Y']

		# Run the CLI command 'codecontext' for each path and capture its output
		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
		stdout, stderr = process.communicate()

		if stderr:
			print("Error from codecontext:")
			print(stderr)
			continue

		if stdout:
			response = stdout.strip()
			total_characters += len(response)
			codecontext_responses.append(response)

	# Join all responses into one string
	llm_query = "\n\n".join(codecontext_responses)
	llm_query = query + "\n\n" + llm_query

	# Log the LLM query
	logging.info(f"LLM Query:\n{llm_query}")

	# Calculate and print output summary
	total_tokens = (total_characters * 10) // 47

	print("-----------------------------------")
	print("          LLM Request            ")
	print("-----------------------------------")
	print(f"  Model: {model}")
	print(f" Tokens: {total_tokens}")
	print("-----------------------------------")

	print("\n-----------------------------------")
	print("          LLM Response           ")
	print("-----------------------------------")

	# Craft the LLM message
	messages = [
		{"role": "system", "content": "You are a programming assistant."},
		{"role": "user", "content": llm_query}
	]

	# Call the OpenAI API using the SDK
	client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
	try:
		stream = client.chat.completions.create(
			model=model,
			messages=messages,
			stream=True,
		)

		response_content = ""

		for chunk in stream:
			if chunk.choices[0].delta.content is not None:
				content = chunk.choices[0].delta.content
				print(content, end="")  # Keep printing to console in real-time
				response_content += content  # Also append to the response_content variable
				sys.stdout.flush()


	except KeyboardInterrupt:
		print("\nStream interrupted by user. Exiting.")
		sys.exit(0)

	# Log the full AI response after collecting it
	logging.info(f"LLM Response:\n{response_content}")
	print("\n-----------------------------------\n\n")
	print("Log file path: ", log_file_path)


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Usage: python codequery.py 'query' [path1] [path2] ...")
		sys.exit(1)

	query = sys.argv[1]
	paths = sys.argv[2:]
	 # Log the user query and paths
	logging.info(f"User Query: {query}, Paths: {', '.join(paths) if paths else 'None'}")
	codequery(query, *paths)
