import pandas as pd
from datetime import timedelta
import re
import srt
import os
import openai
import numpy as np
from openai import OpenAI

class SubtitleParser():
    def __init__(self, en_file_path, tr_file_path, episode):

        self.character_map = {
            'ý': 'ı',
            'Ý': 'İ',
            'ţ': 'ş',
            'þ': 'ş',
            'Þ': 'Ş',
            'Ð': 'Ğ',
            'đ': "ğ",
            'ð': 'ğ',
        }

        self.episode = episode
        self.en_file_path = en_file_path
        self.tr_file_path = tr_file_path
        self.encodings = ["utf-8", "ISO-8859-1", "ISO-8859-9"]

        self.clean_subtitle_data()
        self.client = OpenAI()

    def extract_episode_info(self, file_name):
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are given an example below. Answer in the same format. Example
question: can you give me the episode and the season information from this text: Arrested Development - 04x10 - Queen B. 

answer: season_4_episode_10"""},
                {"role": "user", "content": "can you give me the episode and the season information from this text: "+file_name}
                ]
            )
        
        return completion.choices[0].message.content

    def clean_subtitle_data(self):
        if self.extract_subtitles_from_srt() == False:
            raise Exception("I could not parse your srt files.")

        for sub in self.subtitles_tr:
            sub.content = self.correct_turkish_characters(sub.content)
            if self.contains_only_turkish_characters(sub.content) == False:
                raise Exception("Could not clean turkish characters.")
                    
    def extract_subtitles_from_srt(self):

        encodings = ["utf-8", "ISO-8859-1"]
        for encoding in encodings: 
            try:
                with open(self.en_file_path, encoding=encoding) as f:
                    subtitle_generator = srt.parse(f)
                    self.subtitles_en = list(subtitle_generator)
                    f.close()
            except:
                encodings.remove(encoding)

        if encodings != []:
            with open(self.en_file_path, encoding=encodings[0]) as f:
                subtitle_generator = srt.parse(f)
                self.subtitles_en = list(subtitle_generator)
                f.close()
        
        encodings = self.encodings.copy()
        for encoding in encodings: 
            try:
                with open(self.tr_file_path, encoding=encoding) as f:
                    subtitle_generator = srt.parse(f)
                    self.subtitles_tr = list(subtitle_generator)
                    f.close()
            except:
                encodings.remove(encoding)

        if encodings != []:
            with open(self.tr_file_path, encoding=encodings[0]) as f:
                self.main_turkish_encoding = encodings[0]
                subtitle_generator = srt.parse(f)
                self.subtitles_tr = list(subtitle_generator)
                f.close()
        else:
            return False
        
    def update_file_paths(self, new_path, language):
        if language == "TR":
            self.tr_file_path = new_path
            with open(new_path) as f:
                subtitle_generator = srt.parse(f)
                self.subtitles_tr = list(subtitle_generator)
                f.close()
        elif language == "EN":
            self.en_file_path = new_path
            with open(new_path) as f:
                subtitle_generator = srt.parse(f)
                self.subtitles_en = list(subtitle_generator)
                f.close()
        else:
            raise Exception("Not a valid language.")

    def correct_turkish_characters(self, text):
        for w, c in self.character_map.items():
            text = text.replace(w, c)
        return text

    def contains_only_turkish_characters(self, input_string):
        turkish_regex = re.compile(r'^[  a-zA-ZğĞıİöÖçÇşŞüÜ!\n.,;:´`?≡&#{}@Â\-<>$\d*"\'()wx%]\d*|$')
        if bool(turkish_regex.match(input_string)) == False:
            print(input_string, bool(turkish_regex.match(input_string)))
        return bool(turkish_regex.match(input_string))
    
    def merge_subtitles(self, language, save_path):

        """Merge sentences into srt blocks."""

        if language == "TR":
            subs_list = self.subtitles_tr
            self.tr_file_path = save_path
        elif language == "EN":
            subs_list = self.subtitles_en
            self.en_file_path = save_path
        else:
            raise Exception("Choose something valid!!!")
        
        punctuations = ["!", ".", "?", ":"]
        index = 1
        df_new = pd.DataFrame(columns=["en", "tr"])
        text = ""
        for i, sub in enumerate(subs_list):
            content = sub.content
            content = content.replace("</i>", "").replace("<i>", "").replace("-", "").replace("...", "").replace(" .", ".").replace("\n", " ").replace("{\an8}", "").replace("-->",",").replace("[br]", "")
            if text == "":
                start_time = sub.start
            end_time = sub.end
            text += content + " "

            for punc in punctuations:
                if punc in content[-5:]:
                    new_sub = srt.Subtitle(
                        index=index,
                        start=start_time,
                        end=end_time,
                        content=text,
                        proprietary=''
                    )
                    if i == 0:
                        file_mode = "w"
                    else:
                        file_mode = "a"

                    if new_sub.content != '':
                        if language == "TR":
                            with open(save_path, file_mode) as srtFile:
                                srtFile.write(new_sub.to_srt())
                            self.update_file_paths(save_path, language="TR")
                        else:
                            with open(save_path, file_mode) as srtFile:
                                srtFile.write(new_sub.to_srt())
                            self.update_file_paths(save_path, language="EN")
                        text = ""
                        index += 1

    def sliding_window(self, sub_en, subs_list_tr, moving_index, window_size=7):
        start_en = sub_en.start
        start_idx = 0 if moving_index-window_size < 0 else (moving_index-window_size)
        lowest_time_diff = 10000
        best_match = None
        to_jump = 0

        count = 0
        print("TO MATCH: ", sub_en.content, sub_en.start)
        for writing in subs_list_tr[start_idx:moving_index+window_size]:
            print("CONTENT: "+str(count), writing.content, writing.start)
            count += 1
            
        for i, sub in enumerate(subs_list_tr[start_idx:moving_index+window_size]):
            start_tr = sub.start
            if abs((start_en - start_tr).total_seconds()) < lowest_time_diff and abs((start_en - start_tr).total_seconds()) <= 3.5 and sub.proprietary == '':
                best_match = sub
                sub.proprietary = 'matched'
                to_jump = i
                lowest_time_diff = abs((start_en - start_tr).total_seconds())
            
        print("BEST_MATCH", best_match)

        return best_match, to_jump

    def match_subtitles(self, save_path="sub_csv"):

        flag = "TR" if len(self.subtitles_tr) >= len(self.subtitles_en) else "EN"
        df = pd.DataFrame(columns=["en", "tr"])

        moving_index = 0

        if flag == "TR":
            subs_list = self.subtitles_tr
            for i in range(len(self.subtitles_en)):
                current_sub = self.subtitles_en[i]
                best_match, to_jump = self.sliding_window(current_sub, subs_list, moving_index)
               
                if best_match:
                    df_temp = pd.DataFrame({"en": current_sub.content, "tr": best_match.content}, index=[0])
                    df = pd.concat([df, df_temp], ignore_index=True)
                    moving_index += to_jump
                else:
                    moving_index += 1

        else:
            subs_list = self.subtitles_en
            for i in range(len(self.subtitles_tr)):
                current_sub = self.subtitles_tr[i]
                best_match, to_jump = self.sliding_window(current_sub, subs_list, moving_index)
               
                if best_match:
                    df_temp = pd.DataFrame({"tr": current_sub.content, "en": best_match.content}, index=[0])
                    df = pd.concat([df, df_temp], ignore_index=True)
                    moving_index += to_jump
                else:
                    moving_index += 1

        first = self.en_file_path.split("/")
        title_splits = first[1].split("_")
        df.to_csv(save_path+"/"+title_splits[0]+title_splits[-2]+"_"+title_splits[-1])
        return True
    
def is_contain(arr1, arr2):
    for elem in arr2:
        if arr1[0] == elem[0] and elem[1] == elem[1]:
            return True
    return False 
    
def match_filenames(longer_files, shorter_files, window_size=10):
    count_long = 0
    matched_files = []
    matched_episodes = []
    pattern = "(?<!\d)\d{2}(?!\d)"
    series_patterns = ["[sS]\d{2}[eE]\d{2}", "\d{2}[xX]\d{2}"]

    for j in range(len(shorter_files)):

        episodes = {"LONG":[], "SHORT":[]}
        for m, spattern in enumerate(series_patterns):
            for all in short_files:
                if re.findall(spattern, all):
                    matches = re.findall(spattern, all)[0]
                    if m == 0:
                        episodes["SHORT"].append(matches[1:3]+matches[4:6])
                    else:
                        episodes["SHORT"].append(matches[0:2]+matches[3:5])

            for all in longer_files:
                if re.findall(spattern, all):
                    matches = re.findall(spattern, all)[0]
                    if m == 0:
                        episodes["LONG"].append(matches[1:3]+matches[4:6])
                    else:
                        episodes["LONG"].append(matches[0:2]+matches[3:5])
        
        if episodes["SHORT"] != [] and episodes["LONG"] != []:
            for m, element in enumerate(episodes["SHORT"]):
                if element in episodes["LONG"]:
                    long_index = episodes["LONG"].index(element)

                    short_file_name = shorter_files[m]
                    long_file_name = longer_files[long_index]
                    my_tuple = [long_file_name, short_file_name]
                    if "not" not in long_file_name.lower() and "not" not in short_file_name.lower() and not is_contain(my_tuple, matched_files):
                        matched_files.append(my_tuple)
                        matched_episodes.append(element)
        else:
            short_file = shorter_files[j]
            short_file_nums = re.findall(pattern, short_file)
            start_idx = 0 if j-window_size < 0 else (j-window_size)
            end_idx = len(longer_files)-1 if j+window_size > len(longer_files)-1 else j+window_size

            for element in longer_files[start_idx:end_idx]:
                long_file_nums = re.findall(pattern, element)

                does_correspondence_exist = True

                if len(long_file_nums) > len(short_file_nums):
                    for num in short_file_nums:
                        if num not in long_file_nums:
                            does_correspondence_exist = False
                            break
                else:
                    for num in long_file_nums:
                        if num not in short_file_nums:
                            does_correspondence_exist = False
                            break

                if does_correspondence_exist:
                    if "not" not in element.lower() and "notlar" not in short_file.lower():
                        matched_files.append([element, short_file])
                        text = ""
                        for elm in short_file_nums:
                            text += elm
                        matched_episodes.append(text)
                    break
    return matched_files, matched_episodes


if __name__ == "__main__":

    sub_root = "subs/"
    foldernames = sorted(next(os.walk(sub_root), (None, None, []))[1]) # [] if no file

    done_so_far = []
    for k, folder in enumerate(foldernames):
        print("DOING THIS FOLDER: ", folder)
        foldername_splits = folder.split("_")
        series_name = foldername_splits[0]

        if "EN" in folder:
            en_foldername = folder
            tr_foldername = folder.replace("_EN_", "_TR_")

        for item in sorted(next(os.walk(sub_root+en_foldername), (None, None, []))[2]):
            if item.endswith(".ass") or item.endswith(".sub"):
                os.remove(os.path.join(sub_root+en_foldername, item))

        tr_sub_files = sorted(next(os.walk(sub_root+tr_foldername), (None, None, []))[2])
        en_sub_files = sorted(next(os.walk(sub_root+en_foldername), (None, None, []))[2])
        print(done_so_far)
        if en_foldername not in done_so_far and tr_foldername not in done_so_far:
            done_so_far.append(folder)
            
            if len(tr_sub_files) != len(en_sub_files):
                long_files = tr_sub_files if len(tr_sub_files) > len(en_sub_files) else en_sub_files
                short_files = tr_sub_files if len(tr_sub_files) < len(en_sub_files) else en_sub_files
                long_files_lang = "TR" if len(tr_sub_files) > len(en_sub_files) else "EN"
                matches, episodes = match_filenames(long_files, short_files)
                
                season = foldername_splits[-1]
                for j in range(len(matches)):
                    if long_files_lang == "EN":
                        en_srt = matches[j][0]
                        tr_srt = matches[j][1]
                    else:
                        en_srt = matches[j][1]
                        tr_srt = matches[j][0]

                    en_file_path = os.path.join(sub_root, en_foldername, en_srt)
                    tr_file_path = os.path.join(sub_root, tr_foldername, tr_srt)
                    parser = SubtitleParser(en_file_path, tr_file_path, episode=episodes[j])
                    parser.merge_subtitles("EN", os.path.join("srt_files", folder+"_EN_"+series_name+"_S"+season+"_E"+episodes[j]+".csv"))
                    parser.merge_subtitles("TR", os.path.join("srt_files", folder+"_TR_"+series_name+"_S"+season+"_E"+episodes[j]+".csv"))
                    parser.match_subtitles()

            if k!= 0 and (en_foldername in done_so_far or tr_foldername in done_so_far):
                pass
            else:
                # run the algorithm for each file
                season = foldername_splits[-1]
                for j in range(len(tr_sub_files)):

                    tr_srt = tr_sub_files[j]
                    en_srt = en_sub_files[j]
                    en_file_path = os.path.join(sub_root, en_foldername, en_srt)
                    tr_file_path = os.path.join(sub_root, tr_foldername, tr_srt)
                    parser = SubtitleParser(en_file_path, tr_file_path, episode=j)
                    parser.merge_subtitles("EN", os.path.join("srt_files", folder+"_EN_"+series_name+"_S"+season+"_E"+str(j+1)+".csv"))
                    parser.merge_subtitles("TR", os.path.join("srt_files", folder+"_TR_"+series_name+"_S"+season+"_E"+str(j+1)+".csv"))
                    parser.match_subtitles()
