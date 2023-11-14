#!/bin/bash

#
# Create client certificate 
#

# get filename
read -p "Enter certificate filename (*.pem): " outfile

#
# add .pem if missing.
# 
echo ${outfile} | grep '[.][Pp][Ee][Mm]$' > /dev/null || outfile="${outfile}.pem"

#
# overwrite if exist?
#
if [[ -f ${outfile} ]]
then read -p "File '${outfile}' already exist, Continue and overwrite? (Y/N): " confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] && rm -v ${outfile}
fi 


#
# generate new if doesn't exist
#
if [[ ! -f ${outfile} ]] 
then
	# 
	# create "cert.pem" with key and certificate , valid for 100 years
	#
	echo "Generating key and certificate file: ${outfile}"
	openssl req -new -newkey rsa:2048 -days 36524 -nodes -x509 -keyout ${outfile}  -out ${outfile}  -subj="/" && \
	echo "Created key and certificate file: ${outfile}"
fi



#
# show copy/paste message anyway
#
echo -en "#\n# copy/paste certificate into backend admin: \n# (including ---BEGIN -,  and ----END CERTIFICATE----)\n#\n\n"
awk -v beg='-----BEGIN CERTIFICATE-----' -v end='-----END CERTIFICATE-----' 'sub(".*"beg,beg){f=1} f; sub(end".*",end){exit}' ${outfile}
echo ""

 