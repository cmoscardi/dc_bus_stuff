N=6
(
for thing in `ls data/ | grep -e '2019-[0-9][0-9]-[0-9][0-9]$' | cut -d '-' -f 2 | sort | uniq`; do 
   ((i=i%N)); ((i++==0)) && wait
   python h_street_intervention/h_street_compute.py "$thing" & 
   #echo "$thing"
   #sleep 5 &
done
)
