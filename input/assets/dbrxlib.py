import requests as rq
import datetime as dt
import os
# import applib as al
from .helper import format_event_table
from .helper import format_place_table
from .helper import clean_input
from json import JSONDecodeError

class dbrxlib:
    def __init__(self, token,
                 model = "meta-llama-3-70b-instruct"):
        # assert os.path.isfile(token), "Tzoken file does not exist"
        self.__mdl = model
        self.change_model(model)
        # TODO: How to keep Secrets SECRET
        self.__token = 'dapi332901199cd5c09211e054893ef8bda9'

    ## setters / getters
    def change_model(self, new_model):
        assert new_model in ["dbrx-instruct",
                             "meta-llama-3-70b-instruct",
                             "mixtral-8x7b-instruct",
                             "llama-2-70b-chat"], "Unrecognized Model"
        self.__mdl = new_model

    def model(self):
        return self.__mdl

    def token(self):
        return self.__token

    ## basic prompt function
    def prompt(self, prompt,
               response_type = "full",
               temp = 0.8,
               top = 0.95,
               max = 4000):
        prompt = clean_input(prompt)
        result = rq.post(
            url= f"https://dbc-83763f21-6ef2.cloud.databricks.com/serving-endpoints/databricks-{self.__mdl}/invocations",
            headers={"Content-Type": "application/json"},
            auth=("token", self.__token),
            data='{"messages":[{"role":"user","content":"' +
                 prompt +
                 f'"}}], "temperature":{temp}, "top_p":{top}, "max_tokens":{max}}}')
        if response_type == "full":
            try:
                return result.json()
            except JSONDecodeError:
                return result.content
        elif response_type in result.json()["choices"][0]:
            return result.json()["choices"][0][response_type]
        elif response_type == "pure":
            return result.json()["choices"][0]["message"]["content"]


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

    def ask_binary(self, bin_prompt, rt = "pure"):
        context = self.binary_context()
        full_prompt = context + bin_prompt
        response = self.prompt(full_prompt, response_type = rt)
        if rt != "pure":
            return response
        return response.lower() == "yes"

    def prompt_to_gsearch(self, prompt, rt = "pure"):
        context = self.gsearch_context()
        full_prompt = context + prompt
        response = self.prompt(full_prompt, response_type = rt)
        if rt != "pure":
            return response
        searches = response.split("\n")
        return searches

    def prompt_to_loc_search(self, prompt, rt = "pure"):
        context = self.loc_search_context()
        full_prompt = context + prompt
        response = self.prompt(full_prompt, response_type = rt)
        if rt != "pure":
            return response
        searches = response.split("\n")
        return searches

    def event_table_recommend(self, table, user_prompt):
        table_str = format_event_table(table)
        full_prompt = self.event_endpoint_context(user_prompt, table_str)
        response = self.prompt(full_prompt, response_type = "full")
        counter = 1
        while "error_code" in response:
            if counter > 50:
                raise "ResponseError: Something's out of whack"
            new_table_str = format_event_table(table)
            full_prompt = self.event_endpoint_context(user_prompt,
                                                      new_table_str)
            response = self.prompt(full_prompt, response_type = "full")
            counter += 1
        return response

    def place_table_recommend(self, table, user_prompt):
        table_str = format_place_table(table)
        full_prompt = self.place_endpoint_context(user_prompt, table_str)
        response = self.prompt(full_prompt, response_type = "full")
        counter = 1
        while "error_code" in response:
            if counter > 50:
                raise "ResponseError: Something's out of whack"
            new_table_str = format_place_table(table)
            full_prompt = self.place_endpoint_context(user_prompt,
                                                      new_table_str)
            response = self.prompt(full_prompt, response_type = "full")
            counter += 1
        return response

    def get_date_range(self, user_prompt, rt = "pure"):
        context = self.date_range_context()
        full_prompt = context + user_prompt
        response = self.prompt(full_prompt, response_type = rt)
        if rt != "pure":
            return response
        try:
            dates = response.split(", ")
            date1 = dt.datetime.strptime(dates[0], "%Y-%m-%d")
            date2 = dt.datetime.strptime(dates[1], "%Y-%m-%d")
            return date1, date2
        except:
            return f"Got error: full string: {dates}"