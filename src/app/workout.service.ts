import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

  
@Injectable({
  // we declare that this service should be created
  // by the root application injector.
 
  providedIn: 'root',
})
export class WorkoutService {

  public lapsSource = new Subject<Lap[]>();
  public selectTable:number;
  public nbLaps:number = 0;
  workout$ = this.lapsSource.asObservable();

  pushWorkout(laps: Lap[], selectTable:number) {
    const rows = [];
    this.selectTable = selectTable;
    laps.forEach(element => {rows.push(element, { detailRow: true, element })});
    this.nbLaps = rows.length /2;
    this.lapsSource.next(rows);
  }
  
}

export class Gps {
  gps_index: number;
  gps_lat: number;
  gps_long: number;
  gps_time: number;
  strokeWeight: number;
  color: string;
}

export class Heartrate {
  hr_value: number;
}

export class Activity {
  time: string;
  distance: number;
  resolution: number;
  type: string;
}

export class Split {
  split_index: number;
  split_distance: number;
  split_time: string;
 }

export class Lap {
  lap_index: number;
  lap_start_index: number;
  lap_end_index: number;
  lap_distance: number;
  lap_time: string;
  lap_start_date: string;
  lap_cumulatedTime: string;
  lap_average_speed: number;
  lap_average_HR: number;
  lap_average_cadence: number;
  lap_pace_zone: number;
  lap_total_elevation_gain: number;
  lap_start: number;
  lap_end:number;
}

export class Workout {
  name: string="fli";
  dayTime: string;
  actId: number;
  act: Activity;
  loaded : boolean = false;
  lap: Lap[];
  splits: Split[];
  watchLaps: Lap[];
  splitLaps: Lap[];
  gpsCoord: Gps[];
  heartrate: Heartrate[];
  constructor() {}
}

export interface lapSelection {
  lap_idx: number;
  isCurrent: boolean;
}
