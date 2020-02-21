# download
BASE="https://busdata-00-us-west-2.s3-us-west-2.amazonaws.com/"
for i in {02..12}; do
  for j in {01..31}; do
    wget -nc ${BASE}2019-${i}-${j}.tar.gz
  done
done


# now, unzip
for $fname in `ls *2019*`; do
    tar -xzf $fname;
done
