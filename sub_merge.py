import pandas as pd

csv_filename = "sub_csv/Yeryüzü_season_2_E0.csv"
df = pd.read_csv(csv_filename)
punctuations = ["!", ".", "?", ":"]

df_new = pd.DataFrame(columns=["en", "tr"])
text_en = ""
text_tr = ""
for ind in df.index:
    en_sub = df['en'][ind]
    tr_sub = df['tr'][ind]
    text_en += en_sub + " "
    text_tr += tr_sub + " "

    for punc in punctuations:
        if punc in en_sub and punc in tr_sub:
            df_temp = pd.DataFrame({"en": text_en, "tr": text_tr}, index=[0])
            df_new = pd.concat([df_new, df_temp], ignore_index=True)
            text_en = ""
            text_tr = ""

df_new.to_csv(csv_filename[:-4]+"_merged.sv")
