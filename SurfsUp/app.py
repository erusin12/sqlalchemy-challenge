# Import the dependencies.
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
from flask import Flask, jsonify
from flask import Flask, jsonify, request


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Station = Base.classes.station
Measurement = Base.classes.measurement

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)


#################################################
# Flask Routes
#################################################    
    
"""Start at the homepage."""
@app.route("/")
def home():
    """List all available routes."""
    return """
        Available Routes:<br>
        /api/v1.0/precipitation<br>
        /api/v1.0/stations<br>
        /api/v1.0/tobs<br>
        /api/v1.0/temp/<start><br>
        /api/v1.0/temp/<start>/<end><br>
    """
#Dates must be in YYYY-MM-DD format    

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Convert the query results from precipitation analysis to a dictionary using date as the key and prcp as the value."""
    # Calculate the date one year ago from the last date in the database
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date = dt.date(2017,8,23) - dt.timedelta(days=365)
    one_year_ago = last_date - dt.timedelta(days=365)
    
    # Retrieve the 12 months of precipitation data
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()
    
    # Create a dictionary with date as the key and prcp as the value
    precipitation_data = {date: prcp for date, prcp in results}

    # Return the JSON dictionary
    return jsonify(precipitation_data)


@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""  
    # Retrieve the list of stations  
    results = session.query(Station.station).all()
    
    # Create a list to store the names
    station_list = [result[0] for result in results]
    
    # Return the JSON list
    return jsonify(station_list)
    
@app.route("/api/v1.0/tobs")
def tobs():
    """Query the dates and temperature observations of the most-active station for the previous year of data."""
    # Calculate the date one year ago from the last date in the database
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date = dt.date(2017,8,23) - dt.timedelta(days=365)
    one_year_ago = last_date - dt.timedelta(days=365)

    # Find the most active station
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()
    most_active_station_id = most_active_station[0]

    # Find the temperature observations for the most active station in the last year
    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= one_year_ago).\
        filter(Measurement.station == most_active_station_id).all()

    # Create dictionaries with date and tobs as keys and values
    tobs_data = []
    for date, tobs in results:
        tobs_dict = {"date": date, "tobs": tobs}
        tobs_data.append(tobs_dict)

    # Return the JSON 
    return jsonify(tobs_data)


@app.route("/api/v1.0/temp/<start>")
@app.route("/api/v1.0/temp/<start>/<end>")
def stats(start=None, end=None):
    """Return TMIN, TAVG, TMAX."""
    # Select statement
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    if not end:
        start = dt.datetime.strptime(start, "%Y-%m-%d")
        results = session.query(*sel).\
            filter(Measurement.date >= start).all()
        session.close()
        temps = list(np.ravel(results))
        return jsonify(temps)
    # Calculate TMIN, TAVG, TMAX with start and stop
    start = dt.datetime.strptime(start, "%Y-%m-%d")
    end = dt.datetime.strptime(end, "%Y-%m-%d")
    results = session.query(*sel).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()
    session.close()
    # Unravel results into a 1D array and convert to a list
    temps = list(np.ravel(results))
    return jsonify(temps=temps)

if __name__ == '__main__':
    app.run(debug=True)