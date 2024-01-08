import pysrt
import srt
import os
import pandas as pd
import re

character_map = {
    'ý': 'ı',
    'Ý': 'İ',
    'ţ': 'ş',
    'þ': 'ş',
    'Þ': 'Ş',
    'Ð': 'Ğ',
    'đ': "ğ",
    'ð': 'ğ',
}

save_path = "sub_csv"

def contains_only_turkish_characters(input_string):
    turkish_regex = re.compile(r'^[  a-zA-ZğĞıİöÖçÇşŞüÜ!.,;:?\-<>\d*"\'()wx%]\d*|$')
    if bool(turkish_regex.match(input_string)) == False:
        print(input_string, bool(turkish_regex.match(input_string)))
    return bool(turkish_regex.match(input_string))

def correct_characters(text):
    for w, c in character_map.items():
        text = text.replace(w, c)
    return text

def sliding_window(sub_en, subs_tr, index, window_size=10):
    subs_tr = subs_tr[index:index+window_size]
    for sub in subs_tr:
        # match if less than 2 secs diff
        if (sub.start - sub_en.start).total_seconds() < 2:
            return (sub, sub_en)
        

def merge_subtitles(en_file, tr_file, episode, save_path="sub_csv"):

    subtitles_en = []
    encodings = ["utf-8", "ISO-8859-1", "ISO-8859-9"]
    with open(en_file) as f:
        subtitle_generator = srt.parse(f)
        subtitles_en = list(subtitle_generator)

    subtitles_tr = []
    
    for encoding in encodings: 
        try:
            with open(tr_file, encoding=encoding) as f:
                subtitle_generator = srt.parse(f)
                subtitles_tr = list(subtitle_generator)
        except:
            encodings.remove(encoding)

    if encodings != []:
        with open(tr_file, encoding=encodings[0]) as f:
            subtitle_generator = srt.parse(f)
            subtitles_tr = list(subtitle_generator)
    else:
        return False
    
    flag = "TR" if len(subtitles_tr) >= len(subtitles_en) else "EN"
    df = pd.DataFrame(columns=["en", "tr"])
    tolerance = 2 # in secs
    if len(subtitles_tr) == len(subtitles_en):
        max_check = 1
    else:
        max_check = 3
    if flag == "TR":
        
        count = 0
        for i in range(len(subtitles_en)):
            for j in range(max_check):
                if i != 0 and i+j+count < len(subtitles_tr):
                    sub_tr = subtitles_tr[i+j+count]
                    sub_en = subtitles_en[i]
                    print(abs((sub_en.start - sub_tr.start).total_seconds()) )
                    if abs((sub_en.start - sub_tr.start).total_seconds()) < tolerance:
                        count += j
                        en_content = sub_en.content.replace("<i>", "").replace("</i>", "").replace("\n", " ").replace("-", " ")
                        tr_content = sub_tr.content.replace("<i>", "").replace("</i>", "").replace("\n", " ").replace("-", " ")
                        tr_content = correct_characters(tr_content)
                        is_only_tr = contains_only_turkish_characters(tr_content)
                        
                        if not is_only_tr:
                            return False
                        
                        df_temp = pd.DataFrame({"en": en_content, "tr": tr_content}, index=[0])
                        df = pd.concat([df, df_temp], ignore_index=True)

                else:
                    sub_tr = subtitles_tr[i]
                    sub_en = subtitles_en[i]
                    en_content = sub_en.content.replace("<i>", "").replace("</i>", "").replace("\n", " ").replace("-", " ")
                    tr_content = sub_tr.content.replace("<i>", "").replace("</i>", "").replace("\n", " ").replace("-", " ")
                    tr_content = correct_characters(tr_content)
                    is_only_tr = contains_only_turkish_characters(tr_content)
                    if not is_only_tr:
                        return False
                    df_temp = pd.DataFrame({"en": en_content.replace("...", ""), "tr": tr_content.replace("...", "")}, index=[0])
                    df = pd.concat([df, df_temp], ignore_index=True)
                    break
            exit()
    else:
        count = 0
        for i in range(len(subtitles_tr)):
            for j in range(max_check):
                if i != 0 and i+j+count < len(subtitles_en):
                    sub_tr = subtitles_tr[i]
                    sub_en = subtitles_en[i+j+count]
                    print(len(subtitles_tr))
                    print(abs((sub_en.start - sub_tr.start).total_seconds()) )
                    if abs((sub_en.start - sub_tr.start).total_seconds()) < tolerance:
                        count += j
                        en_content = sub_en.content.replace("<i>", "").replace("</i>", "").replace("\n", " ").replace("-", " ")
                        tr_content = sub_tr.content.replace("<i>", "").replace("</i>", "").replace("\n", " ").replace("-", " ")
                        tr_content = correct_characters(tr_content)
                        is_only_tr = contains_only_turkish_characters(tr_content)
                        if not is_only_tr:
                            return False
                        df_temp = pd.DataFrame({"en": en_content, "tr": tr_content}, index=[0])
                        df = pd.concat([df, df_temp], ignore_index=True)
                else:
                    sub_tr = subtitles_tr[i]
                    sub_en = subtitles_en[i]
                    en_content = sub_en.content.replace("<i>", "").replace("</i>", "").replace("\n", " ")
                    tr_content = sub_tr.content.replace("<i>", "").replace("</i>", "").replace("\n", " ")
                    tr_content = correct_characters(tr_content)
                    is_only_tr = contains_only_turkish_characters(tr_content)
                    if not is_only_tr:
                        return False
                    df_temp = pd.DataFrame({"en": en_content.replace("...", ""), "tr": tr_content.replace("...", "")}, index=[0])
                    df = pd.concat([df, df_temp], ignore_index=True)
                    break

    title_splits = en_file.split("_")
    season_split = title_splits[-1].split("/")
    df.to_csv("./"+save_path+"/"+title_splits[0].replace("subs/", "")+"_season_"+season_split[0]+"_E"+episode+".csv")
    print("./"+save_path+"/"+title_splits[0].replace("subs/", "")+"_season_"+season_split[0]+"_E"+episode+".csv")
    return True

main_folder = "subs/"
foldernames = next(os.walk(main_folder), (None, None, []))[1]

tur_sub_folder = "Avatar:SonHavabükücü_[Un-AiredPilot]iTunes_TR_season_1"
en_sub_folder = "Avatar:SonHavabükücü_[Un-AiredPilot]iTunes_EN_season_1"

# filenames = next(os.walk(main_folder+tur_sub_folder), (None, None, []))[2]
# filenames_en = next(os.walk(main_folder+en_sub_folder), (None, None, []))[2]

filenames = ["19.Bölüm Kuzeyin Kuşatılması (1.Bölüm).srt"]
filenames_en = ["Part 19 The Siege of The North (Part 1).srt"]

for j, filename in enumerate(filenames):
    
    is_done = merge_subtitles(main_folder+en_sub_folder+"/"+filenames_en[j], main_folder+tur_sub_folder+"/"+filename, episode=str(j), save_path=save_path)
    if not is_done:
        print("Skipping: ", en_sub_folder+"/"+filename)
    else:
        print("Done")

# tur_sub_folder = "Avatar:SonHavabükücü_[Un-AiredPilot]iTunes_TR_season_1"
# en_sub_folder = "Avatar:SonHavabükücü_[Un-AiredPilot]iTunes_EN_season_1"

# # filenames = next(os.walk(main_folder+tur_sub_folder), (None, None, []))[2]
# # filenames_en = next(os.walk(main_folder+en_sub_folder), (None, None, []))[2]

# filenames = ["Yeryüzü_KiSS_TR_season_2/BBC.Planet.Earth.The.Future.2006.DVDRiP.KiSS.CD1.srt"]
# filenames_en = ["Yeryüzü_KiSS_EN_season_2/BBC.Planet.Earth.The.Future.2006.DVDRiP.KiSS.CD1.srt"]

# for j, filename in enumerate(filenames):
    
#     is_done = merge_subtitles(filenames_en[j], filename, episode=str(j), save_path=save_path)
#     if not is_done:
#         print("Skipping: ", en_sub_folder+"/"+filename)
#     else:
#         print("Done")
