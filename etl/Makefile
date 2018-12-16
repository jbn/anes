CB := data/clean/anes_cb.json
DF := data/clean/anes.tsv
CB_TXT := data/raw/anes_timeseries_cdf_codebook_var.txt
RAW_DF_FILE := anes_timeseries_cdf_rawdata.txt
RAW_DF := data/raw/$(RAW_DF_FILE)


$DF: $(CB) $(RAW_DF) extract_df.py df_pipeline.py
	./extract_df.py


$(RAW_DF):
	@echo "Download zipfile from:" 
	@echo "   https://electionstudies.org/anes_timeseries_cdf/"
	@echo "Unzip it and move:"
	@echo "   $(RAW_DF_FILE)"
	@echo "to:"
	@echo "   $(RAW_DF)"


$(CB): $(CB_TXT) extract_codebook.py codebook_pipeline.py
	@mkdir -p data/clean
	./extract_codebook.py


$(CB_TXT):
	@mkdir -p data/raw
	wget \
		https://electionstudies.org/wp-content/uploads/2018/12/anes_timeseries_cdf_codebook_var.txt \
		-O $(CB_TXT)
		
