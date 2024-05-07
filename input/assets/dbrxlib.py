import datetime as dt
from .helper import format_event_table
from .helper import format_place_table
from langchain_community.llms import Databricks
from dotenv import load_dotenv
load_dotenv()

class dbrxlib:
    def __init__(self,
                 model = "meta-llama-3-70b-instruct"):
        # assert os.path.isfile(token), "Tzoken file does not exist"
        self.__llm = Databricks(endpoint_name = f"databricks-{model}",
                                transform_input_fn = self.transform_input,
                                extra_params = {"temperature": 0.8, "top_p": 0.95, "max_tokens": 4000})

    ## setters / getters
    def change_model(self, new_model):
        assert new_model in ["dbrx-instruct",
                             "meta-llama-3-70b-instruct",
                             "mixtral-8x7b-instruct",
                             "llama-2-70b-chat"], "Unrecognized Model"
        self.__llm = Databricks(endpoint_name = f"databricks-{new_model}",
                                transform_input_fn = self.transform_input,
                                extra_params = {"temperature": 0.8, "top_p": 0.95, "max_tokens": 4000})

    @staticmethod
    def transform_input(**request):
        newjson = {"messages": [{"role": "user",
                                 "content":request["prompt"]}],
                   "temperature": request["temperature"],
                   "top_p": request["top_p"],
                   "max_tokens": request["max_tokens"]}
        return newjson

    ## basic prompt function
    def prompt(self, prompt):
        response = self.__llm(prompt)
        return response


    @staticmethod
    def gsearch_context():
        date = dt.date.today()
        datestr = date.strftime("%a, %dth %B, %Y")
        context_str = (f"Today is {datestr}. Below is a message from a user who is looking for "
                       "something to do. Using their message generate a series of appropriate "
                       "google searches to obtain the most relevant information relating to "
                       "their message. Return each search on a new line. Use no punctuation. Do not number the list. "
                       "Return only the list with only the requested formatting and NOTHING ELSE.\\n\\n")
        return context_str

    @staticmethod
    def loc_search_context():
        context_str = ("Below is a message from a user who is looking for somewhere to go. Using their message "
                       "generate a series of appropriate google searches for locations that this user might be "
                       "interested in. Return each search on a new line. Use no punctuation. Do not number the list. "
                       "Return only the list with only the requested formatting and NOTHING ELSE.\\n\\n")
        return context_str

    @staticmethod
    def binary_context():
        context_str = ("Respond to the following question with ONLY a single word, 'yes' or 'no'. "
                       "Include NOTHING ELSE in your response:\\n\\n")
        return context_str

    @staticmethod
    def event_endpoint_context(user_prompt, formatted_table):
        context_str = (f"Below is a request from a user and list of events. Using the list of events respond "
                       f"to the user's prompt as best you can. Pretend you did all the work to find and "
                       f"collate the events provided. Make sure to include relevant links "
                       f"for your recommendations. Use only the information supplied, "
                       f"do not use any a priori knowledge you may have. A colleague of yours named SpotBot is "
                       f"working on recommending locations, so keep your recommendations to events only."
                       f"\\n\\nUser Request:\\n{user_prompt}\\n\\nEvents:\\n{formatted_table}")
        return context_str

    @staticmethod
    def place_endpoint_context(user_prompt, formatted_table):
        context_str = (f"Below is a request from a user and list of locations. Using the list of locations "
                       f"respond to the user's prompt as best you can. Pretend you did all the work to find and collate "
                       f"the locations provided. Include any relevant information about the locations you select in "
                       f"your response. Use only the provided information and no a priori knowledge you may have. "
                       f"A colleague of yours named EventBot is working on recommending events, so keep your "
                       f"recommendations to locations only."
                       f"\\n\\nUser Request:\\n{user_prompt}\\n\\nLocations:\\n{formatted_table}")
        return context_str

    @staticmethod
    def date_range_context():
        date_str = dt.date.today().strftime("%a, %dth %B, %Y")
        context_str = (f"Today is {date_str}. Give the date range described in the text below in the following "
                       f"format:\\n\\nYYYY-MM-DD, YYYY-MM-DD\\n\\nIf the date range is unclear "
                       f"use your best judgement. Return NOTHING ELSE.\\n\\nText:\\n\\n")
        return context_str

    def ask_binary(self, bin_prompt):
        context = self.binary_context()
        full_prompt = context + bin_prompt
        response = self.prompt(full_prompt)
        return response

    def prompt_to_gsearch(self, prompt):
        context = self.gsearch_context()
        full_prompt = context + prompt
        response = self.prompt(full_prompt)
        response = response.split("\n")
        return response

    def prompt_to_loc_search(self, prompt):
        context = self.loc_search_context()
        full_prompt = context + prompt
        response = self.prompt(full_prompt)
        response = response.split("\n")
        return response

    def event_table_recommend(self, table, user_prompt):
        table_str = format_event_table(table)
        full_prompt = self.event_endpoint_context(user_prompt, table_str)
        response = self.prompt(full_prompt)
        return response

    def place_table_recommend(self, table, user_prompt):
        table_str = format_place_table(table)
        full_prompt = self.place_endpoint_context(user_prompt, table_str)
        response = self.prompt(full_prompt)
        return response

    def get_date_range(self, user_prompt, rt = "pure"):
        context = self.date_range_context()
        full_prompt = context + user_prompt
        response = self.prompt(full_prompt)
        try:
            dates = response.split(", ")
            date1 = dt.datetime.strptime(dates[0], "%Y-%m-%d")
            date2 = dt.datetime.strptime(dates[1], "%Y-%m-%d")
            return date1, date2
        except:
            return f"Got error: full string: {dates}"