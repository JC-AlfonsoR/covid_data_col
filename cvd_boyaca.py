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