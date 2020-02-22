import glob
import json
import os


import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

from datetime import datetime

START = (38.900192, -77.042114)
END = (38.900189, -77.031378)
start_gdf = gpd.GeoDataFrame({"geometry": gpd.GeoSeries([Point(START[::-1]),
                                                         Point(END[::-1])])})
start_gdf.crs = {"init": "epsg:4326"}
start_gdf = start_gdf.to_crs(epsg=3857)
BUSES = ["30N", "30S", "32", "33", "36"]


def process_json(fname):
    if os.path.getsize(fname) == 0:
        return []
    try:
        with open(fname) as f:
            data = json.load(f)
            if set(data.keys()) != set(['BusPositions']):
                raise Exception("Other keys? {}".format(set(data.keys())))
            return data['BusPositions']
    except Exception as e:
        print(fname, e)
        return []
    
def load_day(day):
    df = pd.concat((pd.DataFrame(process_json(x)) for x in  glob.glob("data/"+day +"/*.json")), ignore_index=True)
    garr = gpd.points_from_xy(df["Lon"], df["Lat"])
    gdf = gpd.GeoDataFrame(df, geometry=garr)
    gdf.crs = {'init' :'epsg:4326'}
    gdf = gdf.to_crs(epsg=3857)
    gdf["dt"] = pd.to_datetime(gdf["DateTime"], errors='coerce')
    return gdf


def h_street_filter(g):
    filt1 = g[(g.geometry.y > 4707380) & (g.geometry.y < 4707450)\
              & (g.geometry.x > start_gdf.loc[0].geometry.x) & (g.geometry.x < start_gdf.loc[1].geometry.x)]
    if np.abs(filt1.geometry.x.min() - filt1.geometry.x.max()) > 400:
        return filt1
    else:
        return []

def i_street_filter(g):
    filt1 = g[(g.geometry.y > 4707540) & (g.geometry.y < 4707600)\
              & (g.geometry.x > start_gdf.loc[0].geometry.x) & (g.geometry.x < start_gdf.loc[1].geometry.x)]
    if np.abs(filt1.geometry.x.min() - filt1.geometry.x.max()) > 400:
        return filt1
    else:
        return []

def process_trip(g):
    h_street_records = h_street_filter(g)
    i_street_records = i_street_filter(g)
    if len(h_street_records) > 0 and len(i_street_records) > 0:
        bad_ids.append(str(g.name) + "," + "many")
        return (None)
    if len(h_street_records) == 0 and len(i_street_records) == 0:
        bad_ids.append(str(g.name) + "," + "none")
        return (None)
    retval = ('h', h_street_records) if len(h_street_records) > 0 else ('i', i_street_records)
    retval[1]["corridor"] = retval[0]
    return retval[1].reset_index()

FEET_PER_METER = 3.28084
def segment_speed(g):
    if len(g) < 3:
        return -1
    start_ix, end_ix = g["dt"].idxmin(), g["dt"].idxmax()
    dist = (FEET_PER_METER * g.loc[start_ix]["geometry"].distance(g.loc[end_ix]["geometry"]))
    time = g.loc[end_ix]["dt"] - g.loc[start_ix]["dt"]
    return (dist, time.total_seconds(), dist / time.total_seconds(),
            g["corridor"].unique()[0], len(g), g.loc[start_ix]["dt"], g.loc[end_ix]["dt"])

SEGMENT_SPEED_COLUMNS = ['TripID', 'distance', 'time', 'rate', 'corridor', 'n', 'start_t', 'end_t']


bad_ids = []
def main(month):
    global bad_ids
    dates = [x for x in os.listdir("data/")\
             if x.startswith("2019-{}".format(month)) and ".tar.gz" not in x]

    for date in sorted(dates)[1:]:
        if date + ".csv" in os.listdir("output"):
            print("skipping date {}...".format(date))
            #continue
        print("Processing date {}".format(date))
        try:
            gdf = load_day(date)
        except Exception as e:
            print("Error in date {}".format(date))
            raise e
        interesting = gdf[gdf["RouteID"].isin(BUSES)]
        bad_ids = []
        results = interesting.groupby("TripID").apply(process_trip)
        print("{}/{} processed".format(results.reset_index(level=1).index.nunique(), interesting.TripID.nunique()))
        print("{} bad_ids".format(len(bad_ids)))
        print("=====" * 4)
        with open("output/{}_bad.csv".format(date), "w+") as bad_ids_f:
            bad_ids_f.write("\n".join(bad_ids))

        rst = results.reset_index(level=1)
        del rst["level_1"]
        x = rst.reset_index(drop=True).groupby("TripID").apply(segment_speed).apply(pd.Series).reset_index()
        x.columns = SEGMENT_SPEED_COLUMNS
        x.to_csv("output/{}.csv".format(date))

if __name__ == "__main__":
    import sys
    month = sys.argv[1]
    main(month)
