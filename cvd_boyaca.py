def get_data():
	'''get_data
	df, nombres_provincias, download_date = get_data()

	Downloads data from www.datos.gov.co
	returns
	df [pd.Dataframe] --- Cleaned data from www.datos.gov.co
	nombres_provincias [pd.Dataframe] --- Names of "municipios & provincias" in caps and proper dialect. Includes wikipedia urls to flags pngs
	download_date [datetime] --- Date & time when data was downloaded
	'''

	from sodapy import Socrata
	from datetime import datetime
	import pandas as pd
	import numpy as np

	print("*"*30 + "\n", "Downloading data" + "\n"+"*"*30)
	# -------------------------------------------------------------
	# -------------------------------------------------------------
	# Download Data from www.datos.gov.co -------------------------
	# -------------------------------------------------------------
	# -------------------------------------------------------------


	# Code Snippet taken from
	# https://dev.socrata.com/foundry/www.datos.gov.co/gt2j-8ykr
	#
	# Useful documentation
	# https://dev.socrata.com/docs/filtering.html

	# Unauthenticated client only works with public data sets. Note 'None'
	# in place of application token, and no username or password:
	client = Socrata("www.datos.gov.co", None)

	# First 2000 results, returned as JSON from API / converted to Python list of
	# dictionaries by sodapy.
	q1 = "departamento=15"
	results = client.get("gt2j-8ykr", where=q1, limit=1000000)
	download_date = datetime.now() # Record date & time of data donwnload


	# Convert to pandas DataFrame
	results_df = pd.DataFrame.from_records(results)

	print("Data download date & time \n", download_date,"\n"*2)
	results_df.info()

	# Write date & Number of rows into n_reg.csv
	n_rows,n_cols = results_df.shape
	file_object = open('n_reg.csv', 'a')
	n_entry = download_date.strftime('%d/%m/%y %H:%M') + "," + str(n_rows) + "\n"
	print("\n"*2+"Writing to n_reg.csv \n--->", n_entry)
	file_object.write(n_entry)
	file_object.close()

	# Write data to file
	#results_df.to_csv('raw_data.csv')
	print("*"*30+"\n" + "Finish" + "\n"+"*"*30)



	
	print("*"*30 + "\n", "Clean & Merge" + "\n"+"*"*30)

	# Load Data
	df = results_df.copy()	
	nombres_provincias = pd.read_csv("nombres_provincias_tildes.csv")


	# Drop columns
	drop_columns = ["departamento", 
	                "departamento_nom", 
	                "ciudad_municipio",
	                "unidad_medida", 
	                "per_etn_", 
	                "nom_grupo_",
	                "pais_viajo_1_cod",
	                "pais_viajo_1_nom",
	                "sexo",
	                "fuente_tipo_contagio",
	                "ubicacion",
	                "estado",
	                "tipo_recuperacion"
	               ]
	df = df.drop(columns=drop_columns)

	# Transform dates to datetime objects using the propper format
	dates = ["fecha_reporte_web", 
	         "fecha_de_notificaci_n", 
	         "fecha_inicio_sintomas", 
	         "fecha_muerte", 
	         "fecha_diagnostico", 
	         "fecha_recuperado"
	        ]
	formated_dates = ["f_reporte_web", 
	                  "f_notificacion", 
	                  "f_ini_sintomas", 
	                  "f_muerte", 
	                  "f_diagnostico", 
	                  "f_recuperacion"
	                 ]
	print("\n*** Formating Dates")
	for i in range(len(dates)):
	    print(dates[i], "\t\t--->", formated_dates[i])
	    df[formated_dates[i]] = pd.to_datetime( df[dates[i]], format='%d/%m/%Y %H:%M:%S' )

	df = df.drop(columns=dates) # Drop obsolete columns

	print("\n*** Convert 'edad' from str to ints")
	df["edad"] = df["edad"].astype(int)

	# "Estado" column has NaN values for some cases with a valid pass-away date
	# Correct those NaN with "Fallecido"
	number_of_nans = np.sum(df["recuperado"]=="N/A")
	print("\n*** Number of Nans in 'recuperado' column = ", number_of_nans)
	if number_of_nans != 0:
	    row_indexer = ~df["f_muerte"].isna() # rows with valid pass-away dates
	    df.loc[ (row_indexer) , "recuperado" ] = "Fallecido" # Fix value for "Recuperado" column
	    print("-->Correction of 'fallecido' value in 'recuperado' column for ", np.sum(row_indexer), "rows")
	    
	    number_of_nans = np.sum(df["recuperado"]=="N/A")
	    print("After correction there are still ", number_of_nans, "N/A observations\n")
	    print("Dropping the following observations\n")
	    print(df.loc[df["recuperado"]=="N/A",["id_de_caso","ciudad_municipio_nom","f_muerte","recuperado"]])
	    df = df.drop( df[ df["recuperado"]=="N/A" ].index )
	else:
	    print("--> No Correction required\n" + "--- warning --- "*5 + "\nPlease verify lines 106-118")
	    # There should be more than 300 missing values
	    # Usual error: N/A loaded in a different way
	    # SO line 106 not wotking properly

	# Add Provincias names
	df = df.merge(nombres_provincias, on="ciudad_municipio_nom", how='left')
	#df = df.drop(columns=["municipio_tildes","provincia_tildes"])
	print("\n")
	print(df.info())


	print("\n*** Most recent reported dates\n", df.loc[:,formated_dates].max())
	#df = df.drop(columns=["f_reporte_web","f_notificacion"])

	
	print("\n"+"*"*30 + "\n", "Finish" + "\n"+"*"*30)
	
	return df, nombres_provincias, download_date

def export_to_flourish():
	# Export the time series of number of notified cases by town

	"""
	df.info()
	# f_reporte_web and f_notificacion are the only complete columns containing dates

	# Explore relationships between dates
	df["diff"] = (df["f_reporte_web"] - df["f_notificacion"]) / np.timedelta64(1, 'D')
	print("All data\n", df["diff"].describe(), "\n\n")
	print("When f_reporte_web > f_notification\n", df.query("diff>0")["diff"].describe())

	# Print the anomalous data
	df.query("diff<0").head(20)

	#The expected behavior is first notify, then report on the web
	#For the above few observations it was reversed. It Might be an error. 
	#Time discrepancies for 9 observations out of >70k is not significant in the graphics. So, I am going to process the Floursih data based on notitification date

	"""
	import os
	import numpy as np
	import pandas as pd
	from cvd_boyaca import get_data

	# Get data
	df, nombres_provincias, download_date = get_data()
	# Data to export to Flourish
	# Create time series of new cases


	# Create acumulate time series using pivot tables
	notified_cases = df.pivot_table(index="f_notificacion", 
	                                  values="id_de_caso", 
	                                  columns="ciudad_municipio_nom", 
	                                  aggfunc=np.count_nonzero)
	cum_notified_cases = notified_cases.sort_index(ascending=True).cumsum()


	# Resample time series
	d_min = df["f_notificacion"].min()
	d_max = df["f_notificacion"].max()
	t_index = pd.date_range(start=d_min, end=d_max, freq='D')
	print("Initial & Final Dates", d_min, d_max, sep="\n")

	# Use pad() to fill NaN values to the front and fillna(0) to fill the remaining NaN with 0
	r_cum_notified_cases = cum_notified_cases.reindex(t_index).pad().fillna(0)

	# Print date interval
	d_min = df["f_reporte_web"].min()
	d_max = df["f_reporte_web"].max()
	print("Initial & Final Dates", d_min, d_max, sep="\n")

	# Check for NaNs
	print(r_cum_notified_cases.isna().any(), "\n")
	print(r_cum_notified_cases.isna().any().any())


	# Transpose data because Flourish requires each town as a row
	# Merge with nombres_provincias to load names, procincias and flag url
	to_flourish = r_cum_notified_cases.T.merge(nombres_provincias, on="ciudad_municipio_nom", how='left')
	to_flourish_p1000c = to_flourish.copy()
	to_flourish_p1000c.iloc[:,1:-5] = to_flourish_p1000c.iloc[:,1:-5].div(to_flourish_p1000c.Poblacion_2020/1000, axis=0) # cases per 1000 hab

	to_flourish = to_flourish.reset_index().drop(columns="index")
	to_flourish_p1000c = to_flourish_p1000c.reset_index().drop(columns="index")

	# Tag the top 6 towns
	#index_top6 = to_flourish["ciudad_municipio_nom"].isin(top6)
	#to_flourish.loc[index_top6,"provincia_mayuscula"] = "TOP 6"
	#to_flourish.loc[index_top6,"provincia_tildes"] = "Municipios con más Casos"

	print("*"*30 + "\nTime Series exported\n" + "*"*30)
	# Write CSV File
	to_flourish.to_csv("timeSeries_Boyaca.csv")
	to_flourish_p1000c.to_csv("timeSeries_p1000c_Boyaca.csv")

	# Use terminal commands to delete 00:00:00 from the dates
	os.system( "sed 's/00\\:00\\:00//g' timeSeries_Boyaca.csv -i")
	os.system( "sed 's/00\\:00\\:00//g' timeSeries_p1000c_Boyaca.csv -i")
