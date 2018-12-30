import { Component, ElementRef, HostListener, ViewChild, OnInit, AfterViewInit, 
  OnChanges, SimpleChanges, ChangeDetectorRef, Input, Output, Inject, EventEmitter } from '@angular/core';
import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';
import { CollectionViewer, DataSource } from '@angular/cdk/collections';
import { GoogleMapsAPIWrapper, AgmMap, LatLngBounds, LatLngBoundsLiteral, MapsAPILoader } from '@agm/core';
import { animate, state, style, transition, trigger } from '@angular/animations';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material';
import { Chart } from 'chart.js';
import { jqxChartComponent } from 'jqwidgets-scripts/jqwidgets-ts/angular_jqxchart';
import { WorkoutService, Gps, Heartrate, Activity, Lap, Workout, 
  lapSelection, Split } from './workout.service';

declare var google: any;

export interface DialogData {
  showLap: boolean;
  showTrends: boolean;
}

export class myIcone {
  path: string;
  color: string;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  animations: [
    trigger('detailExpand', [
      state('collapsed', style({ height: '0px', minHeight: '0', visibility: 'hidden' })),
      state('expanded', style({ height: '*', visibility: 'visible' })),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)'))
    ]),
  ],
})

export class AppComponent implements AfterViewInit {
  @ViewChild('myChart') myChart: jqxChartComponent;
  title = 'MyStrava';
  /* url : string = 'http://fakarava94.no-ip.org:3000/workout/'; */
  url: string = '/strava2/workoutDetail/';
  wid: string;
  lat: number = 48.832929;
  lng: number = 2.473295;

  x: number;
  y: number;
  px: number;
  py: number;
  width: number;
  height: number;
  minArea: number;
  draggingCorner: boolean;
  draggingWindow: boolean;
  resizer: Function;
  done: number;
  startHour: number;
  selectedWindow: Window;
  newInnerHeight: number;
  newInnerWidth: number;
  clickLapDistance: number;
  clickLapTime: string;
  resolution: number=1000;  // to get from server
  workoutSize:number;
  ratio: number;
  lapSize: number = 0;
  lap_end_index: number = 0;
  lapInfos: infos = new infos();
  infosData: infoTable[] = [
    {title: 'Total time', value: ''},
    {title: 'Average time', value: ''},
    {title: 'Average Pace', value: ''},
    {title: 'Total dist. (km)', value: ''},
  ];
  displayedColumns: string[] = ['title', 'value'];
  showLaps: boolean = true;  
  showTrends: boolean = true;    
  showSettings: boolean = true;  
        
  winLap: Window = new Window(this);
  winTrends: Window = new Window(this);
  winInfos: Window = new Window(this);
  winSettings: Window = new Window(this);

  tables: LapTable[] = [
    {value: 0, viewValue: 'Manual laps'},
    {value: 1, viewValue: 'Custom Laps'},
    {value: 2, viewValue: 'Split Laps'}
  ];
  selectedTable: number=0;  //0: WatchLap, 1: customLap, 2: splitLap
  currentTable: number=0;

  // pin icons
  // square-pin icon
  squarePin: any;
  squarePin2: any;
  currentIcon: any;

  // activity icons

  typeIcon: Array<myIcone> = new Array<myIcone>();
  
  // Charts
  marker: any;
  map: any;
  hrData: Array<number> = new Array<number>();
  hrIdx:  Array<number> = new Array<number>();
  elevationData: Array<number> = new Array<number>();
  speedData: Array<number> = new Array<number>();
  distanceData: Array<number> = new Array<number>();
  toolTipTrends: string;
  splitBegin: number = -1;
  splitBeginIndex: number;
  splitEnd: number;
  currentIndex: number;
  bands = [];
  recessions = [];
  redrawBands: boolean = false;
  currentRecession: number=-1;
  currentX: number=-1;
  saveCurrentX: number=-1;
  padding: any;
  titlePadding: any;
  xAxis: any;
  seriesGroups: any[];
  renderer: any;
  rect: any;
  currentRect: any;
  onChartArea: boolean = false;
  timer: any;
  Ymin:number = 0;
  Ymax:number = 0;

  w1: Workout;
  srv: WorkoutService;

  @ViewChild('AgmMap') agmMap: AgmMap;

  constructor(private http: HttpClient, private eltRef: ElementRef, 
    private mapsAPILoader: MapsAPILoader, public dialog: MatDialog,
    private gmapsApi: GoogleMapsAPIWrapper, 
    private changeDetectorRefs: ChangeDetectorRef,
    private wktService: WorkoutService) {

    this.srv = wktService;
    this.newInnerHeight = window.innerHeight;
    this.newInnerWidth = window.innerWidth;

    this.lapInfos.show = false;
    this.showSettings = false;

    this.updateView();
      
    this.selectedWindow = this.winLap;

    console.log('innerWidth=', window.innerWidth);

    this.done = 0;
    this.wid = localStorage.getItem('wid');
    if (this.wid) {
      localStorage.removeItem('wid');
      console.log('wid=', this.wid);
    } else {
      this.wid = ""
    }

    this.getWorkout();
  }
          
  public getWorkout() {
    
    if (this.wid != "") {
      this.url = this.url + this.wid;
      /*
      this.http.get(this.url).toPromise().then((res) => {
        console.log(res.json());
      });
      */
    } else {
      this.url = 'assets/mockup.json';
    }
      
    this.http.get(this.url).subscribe((w: Workout) => { 
      this.w1 = w;
      console.log('w=',w);

      this.w1.name = w.act[0]['label'];
      this.w1.dayTime = w.act[0]['strTime'];
      this.w1.act.distance = w.act[0]['distance']/1000;
      this.w1.act.type = w.act[0]['type'];
      this.w1.act.time = w.act[0]['time'];
      this.resolution = w.act[0]['resolution'];

      let d: Date = new Date(w.act[0]['strTime']);
      console.log('start_date=',d, d.getTime()/1000);
      this.startHour = d.getHours()*3600+d.getMinutes()*60+d.getSeconds();

      this.w1.gpsCoord = new Array<Gps>();
      w['gps'].forEach(item => {
        let p1: Gps = new Gps();
        // console.log('gps item=',item);
        p1 = {
          gps_index: item.gps_index,
          gps_lat: item.gps_lat,
          gps_long: item.gps_long,
          gps_time: item.gps_time,
          strokeWeight: 2,
          color: '#2196f3'
        };
        this.w1.gpsCoord.push(p1);
      });

      this.w1.lap = new Array<Lap>();
      w['laps'].forEach(item => {
        let l1: Lap = new Lap();
        // console.log('lap item=',item);
        l1 = {
          lap_index: item.lap_index,
          lap_start_index: item.lap_start_index,
          lap_end_index: item.lap_end_index,
          lap_distance: Math.round(item.lap_distance),
          lap_time: item.lap_time,
          lap_start_date: item.lap_start_date,
          lap_cumulatedTime: "00:00:00",
          lap_average_speed: Math.round(item.lap_average_speed*36)/10,
          lap_average_HR: 0,
          lap_average_cadence: item.lap_average_cadence*2,
          lap_pace_zone: item.lap_pace_zone,
          lap_total_elevation_gain: item.lap_total_elevation_gain,
          lap_start: 0,
          lap_end:0
        };
        this.w1.lap.push(l1);
      });
      this.lapSize = this.w1.lap.length;
      this.lap_end_index = this.w1.lap[this.lapSize-1].lap_end_index;
      this.workoutSize = this.w1.lap[this.w1.lap.length-1].lap_end_index;
      this.ratio = this.resolution / this.workoutSize;

      console.log('ratio=', this.ratio);

      this.w1.splits = new Array<Split>();
      w['split'].forEach(item => {
        let s1: Split = new Split();
        // console.log('lap item=',item);
        s1 = {
          split_index: item.split_index,
          split_distance: Math.round(item.split_distance),
          split_time: item.split_time,
        };
        this.w1.splits.push(s1);
      });

      let k:number = 0;
      w['heartrate'].forEach(item => {
        let h1: Heartrate = new Heartrate();
        h1 = {
          hr_value: item.hr_value,
        };
        this.w1.heartrate.push(h1);
        this.hrData.push(item.hr_value);
        this.hrIdx.push(k++);       
      });
      k = 0;
      w['elevation'].forEach(item => {
        this.elevationData.push(Math.round(item.elevation_value*10)/10);
      });
      w['speed'].forEach(item => {
        this.speedData.push(Math.round(item.speed_value*360)/100);
      });
      w['distance'].forEach(item => {
        this.distanceData.push(Math.round(item.distance_value*10)/10);
      });

      this.computeWatchLapIndex(0, 1);

      for (let i =0; i< this.w1.lap.length; i++) {
        let avgHR: number = 0;
        for (let j=this.w1.lap[i].lap_start; j<=this.w1.lap[i].lap_end;j++) {
          avgHR+=this.hrData[j];
        }
        avgHR=avgHR/(this.w1.lap[i].lap_end-this.w1.lap[i].lap_start+1);
        avgHR = Math.trunc(avgHR);
        this.w1.lap[i].lap_average_HR = Math.round(avgHR);
      }

      console.log('w1=', this.w1);
      console.log('lapSize=', this.lapSize);

      // icon for avtivity type
      let ic = new myIcone ();
      ic = {
          path: "M283.733,85.333c23.467,0,42.667-19.2,42.667-42.667C326.4,19.2,307.2,0,283.733,0s-42.667,19.2-42.667,42.667 S260.267,85.333,283.733,85.333zM401.067,245.333v-42.667c-39.467,0-73.6-21.333-92.8-52.267L288,116.267C280.533,103.467,266.667,96,251.733,96 c-5.333,0-10.667,1.067-16,3.2l-112,45.867v100.267H166.4v-71.467l37.333-14.933l-33.067,171.733L66.133,310.4L57.6,352 c0,0,149.333,28.8,149.333,29.867L227.2,288l45.867,42.667v128h42.667V297.6L272,253.867l12.8-64 C312.533,224,354.133,245.333,401.067,245.333z",
          color: "#FFDA44"
      }
      this.typeIcon['Run'] = ic;
      ic = {
          path: "M321.097,112.359c20.973,12.338,47.985,5.315,60.293-15.652c12.34-20.973,5.35-47.974-15.623-60.304   c-21.009-12.332-47.99-5.317-60.314,15.65C293.129,73.036,300.103,100.027,321.097,112.359zM393.081,264.102c-2.414,0-4.8,0.194-7.169,0.362l-14.431-71.605l4.702-1.757c10.666-3.987,16.093-15.868,12.098-26.54   c-3.994-10.681-15.946-16.084-26.531-12.09l-51.823,19.38l-2.321-18.864c6.3-13.193,5.541-29.78-4.767-41.482   c-21.224-24.092-47.12-12.508-55.191-5.976l-106.884,86.555l0.016,0.024c-3.319,2.893-6.089,6.485-7.86,10.842   c-2.191,5.396-2.596,11.067-1.564,16.384c-8.503,0.669-15.255,7.571-15.255,16.246c0,9.085,7.346,16.44,16.432,16.48l-6.797,15.906   c-8.62-2.465-17.674-3.866-27.066-3.866C44.27,264.102,0,308.354,0,362.754c0,54.403,44.27,98.663,98.668,98.663   c54.403,0,98.652-44.26,98.652-98.663c0-36.228-19.683-67.867-48.858-85.024l10.957-25.652h17.767l60.281,24.462l-32.201,52.773   c-8.297,13.612-3.994,31.382,9.615,39.685c4.691,2.86,9.878,4.229,15,4.229c9.729,0,19.234-4.929,24.677-13.838l29.339-48.095   l19.072,11.511c-5.447,12.227-8.54,25.726-8.54,39.95c0,54.403,44.254,98.663,98.652,98.663c54.402,0,98.656-44.26,98.656-98.663   C491.737,308.354,447.483,264.102,393.081,264.102z M98.668,436.671c-40.756,0-73.923-33.161-73.923-73.917   c0-40.756,33.167-73.909,73.923-73.909c5.944,0,11.649,0.896,17.188,2.224l-20.476,47.893   c-11.758,1.619-20.843,11.598-20.843,23.792c0,13.323,10.808,24.132,24.13,24.132c8.767,0,16.367-4.745,20.589-11.76h52.065   C165.395,409.988,135.188,436.671,98.668,436.671z M171.322,350.383h-52.065c-0.355-0.588-0.708-1.176-1.112-1.732l20.476-47.901   C155.679,311.776,167.793,329.595,171.322,350.383z M296.781,290.175l7.666-12.564c4.416-7.233,5.431-16.038,2.774-24.084   c-2.661-8.046-8.718-14.515-16.562-17.704l-52.725-21.395l32.443-26.281l1.804,14.691c0.756,6.267,4.366,11.841,9.761,15.12   c3.271,1.981,6.979,2.988,10.698,2.988c2.435,0,4.88-0.435,7.218-1.306l48.15-18.001l13.627,67.691   c-18.268,6.162-34.117,17.51-45.848,32.314L296.781,290.175z M375.396,337.633l-38.003-22.94   c7.877-9.118,17.787-16.319,29.205-20.734L375.396,337.633z M393.081,436.671c-40.757,0-73.907-33.161-73.907-73.917   c0-9.544,1.965-18.597,5.268-26.983l44.541,26.888c0,0.032-0.016,0.064-0.016,0.095c0,13.323,10.808,24.132,24.114,24.132   c13.322,0,24.118-10.81,24.118-24.132c0-10.478-6.721-19.307-16.06-22.64l-10.277-51.043c0.756-0.024,1.463-0.226,2.22-0.226   c40.757,0,73.911,33.153,73.911,73.909C466.992,403.51,433.838,436.671,393.081,436.671z",
          color: "#006DF0"
      }
      this.typeIcon['Ride'] = ic;
      ic = {
          path: "M170.667,128.002l-69.333,69.333c6.613,2.56,11.947,5.653,16.427,8.32c7.893,4.8,12.693,7.68,24.533,7.68     c11.84,0,16.64-2.88,24.533-7.573c9.6-5.76,22.827-13.76,46.507-13.76s36.907,7.893,46.507,13.76     c7.893,4.8,12.693,7.573,24.533,7.573c11.84,0,16.64-2.88,24.533-7.573c2.56-1.6,5.44-3.2,8.64-4.907L180.907,64.002     C147.733,30.828,117.333,21.122,64,21.335v53.333c38.827-0.213,61.547,8.32,85.333,32L170.667,128.002zM401.92,259.095c-9.6-5.867-22.827-13.76-46.507-13.76s-36.907,8-46.507,13.76c-7.893,4.693-12.693,7.573-24.533,7.573     c-11.84,0-16.64-2.773-24.533-7.573c-9.6-5.867-22.827-13.76-46.507-13.76s-36.907,8-46.507,13.76     c-7.893,4.693-12.693,7.573-24.533,7.573c-11.947,0-16.747-2.88-24.64-7.68c-9.6-5.76-22.827-13.653-46.507-13.653     s-36.907,7.893-46.507,13.653c-8,4.8-12.8,7.68-24.64,7.68v42.667c23.68,0,36.907-7.893,46.507-13.653     c8-4.8,12.693-7.68,24.64-7.68s16.747,2.88,24.64,7.68c9.6,5.76,22.827,13.653,46.507,13.653s36.907-7.893,46.72-13.76     c7.893-4.693,12.693-7.573,24.533-7.573c11.84,0,16.64,2.773,24.533,7.573c9.6,5.867,22.827,13.76,46.507,13.76     c23.68,0,36.907-8,46.507-13.76c7.893-4.693,12.693-7.573,24.533-7.573c11.84,0,16.64,2.88,24.533,7.573     c9.6,5.867,22.827,13.76,46.507,13.76v-42.667C414.827,266.668,410.027,263.788,401.92,259.095zM355.413,341.335c-23.68,0-36.907,8-46.507,13.76c-7.893,4.693-12.693,7.573-24.533,7.573     c-11.84,0-16.64-2.773-24.533-7.573c-9.6-5.867-22.827-13.76-46.507-13.76s-36.907,8-46.507,13.76     c-7.893,4.693-12.693,7.573-24.533,7.573c-11.947,0-16.747-2.88-24.64-7.68c-9.6-5.76-22.827-13.653-46.507-13.653     s-36.907,7.893-46.507,13.653c-8,4.8-12.8,7.68-24.64,7.68v42.667c23.68,0,36.907-7.893,46.507-13.653     c8-4.8,12.693-7.68,24.64-7.68s16.747,2.88,24.64,7.68c9.6,5.76,22.827,13.653,46.507,13.653s36.907-7.893,46.72-13.76     c7.893-4.693,12.693-7.573,24.533-7.573c11.84,0,16.64,2.773,24.533,7.573c9.6,5.867,22.827,13.76,46.507,13.76     c23.68,0,36.907-8,46.507-13.76c7.893-4.693,12.693-7.573,24.533-7.573c11.84,0,16.64,2.88,24.533,7.573     c9.6,5.867,22.827,13.76,46.507,13.76v-42.667c-11.84,0-16.64-2.88-24.747-7.573C392.32,349.228,379.093,341.335,355.413,341.335z",
          color: "#91DC5A"
      }
      this.typeIcon['Swimm'] = ic;
 
      if ( this.w1.act.type == "" ) {
        this.w1.act.type = 'Run';
      }

      this.done = 1;
      this.w1.loaded = true;

      this.displayTrends();

    });

  }

  computeWatchLapIndex ( startIdx: number, correction: number ) {
    let j:number;
    let idx = startIdx;
    let t: Date = new Date(this.w1.lap[0].lap_start_date);
    let curTime:number=t.getTime()/1000;
    let splitTime=this.w1.gpsCoord[startIdx].gps_time;
    let computeLapTime=0;
    for(j = 0;j<this.w1.lap.length;j++) {
      // this.w1.lap[j].lap_start = Math.round(this.w1.lap[j].lap_start_index*this.ratio);
      // this.w1.lap[j].lap_end = Math.round(this.w1.lap[j].lap_end_index*this.ratio);
      this.w1.lap[j].lap_start = idx;
      // let t: Date = new Date('1970-01-01T' + this.w1.lap[j].lap_time + 'Z');
      if (j<this.w1.lap.length-1) {
          let t2: Date = new Date(this.w1.lap[j+1].lap_start_date);
          splitTime += t2.getTime()/1000 - curTime;
          computeLapTime = t2.getTime()/1000 - curTime;
          curTime = t2.getTime()/1000;
          let hh:number = Math.trunc(computeLapTime/3600);
          let mm:number = Math.trunc(computeLapTime/60)-hh*60;
          let ss:number = computeLapTime-hh*3600-mm*60;
          this.w1.lap[j].lap_time = String(hh).padStart(2, '0') + ':' +
            String(mm).padStart(2, '0') +':' + String(ss).padStart(2, '0');
      } else {
          let t2: Date = new Date('1970-01-01T' + this.w1.lap[j].lap_time + 'Z');
          console.log ('init, t2=',t2);
          splitTime += t2.getTime()/1000;
      }
      
      // console.log('lap ',j+1,'lap_time=',this.w1.lap[j].lap_time, 
      //  'splitTime=',splitTime, 'idx=',this.binaryIndexOf(splitTime, correction));
      let hh:number = Math.trunc(splitTime/3600);
      let mm:number = Math.trunc(splitTime/60)-hh*60;
      let ss:number = splitTime-hh*3600-mm*60;
      this.w1.lap[j].lap_cumulatedTime = String(hh).padStart(2, '0') + ':' +
        String(mm).padStart(2, '0') +':' + String(ss).padStart(2, '0');
      idx = this.binaryIndexOf(splitTime, correction);
      this.w1.lap[j].lap_end = idx;
      // console.log('lap_end=', this.w1.lap[j].lap_end);
    }
  }

  updateView () {
    this.winLap.x = 50;
    this.winLap.y = 130;
    this.winLap.px = 0;
    this.winLap.py = 0;
    this.winLap.width = 300;
    this.winLap.height = 500;
    this.winLap.draggingCorner = false;
    this.winLap.draggingWindow = false;
    this.winTrends.minArea = 20000

    this.winTrends.x = window.innerWidth - 0.75 * window.innerWidth - 10;
    this.winTrends.y = window.innerHeight - 0.2 * window.innerHeight - 10;
    this.winTrends.px = 0;
    this.winTrends.py = 0;
    this.winTrends.width = 0.70 * window.innerWidth;
    this.winTrends.height = 0.2 * window.innerHeight;
    this.winTrends.draggingCorner = false;
    this.winTrends.draggingWindow = false;
    this.winTrends.minArea = 20000;

    this.winInfos.x = 50;
    this.winInfos.y = window.innerHeight - 0.2 * window.innerHeight - 10;
    this.winInfos.px = 0;
    this.winInfos.py = 0;
    this.winInfos.width = 300;
    this.winInfos.height = 102;
    this.winInfos.draggingCorner = false;
    this.winInfos.draggingWindow = false;
    this.winInfos.minArea = 20000;

    this.winSettings.x = window.innerWidth - 0.1 * window.innerWidth - 50;
    this.winSettings.y = 50;
    this.winSettings.px = 0;
    this.winSettings.py = 0;
    this.winSettings.width = 0.1 * window.innerWidth;
    this.winSettings.height = 0.2 * window.innerHeight;
    this.winSettings.draggingCorner = false;
    this.winSettings.draggingWindow = false;
    this.winSettings.minArea = 20000;

  }

  fitToScreen(event) {
    console.log('event=',event);
    const bounds: LatLngBounds = new google.maps.LatLngBounds();
    for (const mm of this.w1.gpsCoord) {
      bounds.extend(new google.maps.LatLng(mm.gps_lat, mm.gps_long));
    }
    console.log('bounds=', bounds);
    /* event.setZoom(event.zoom - 2); */
    event.fitBounds(bounds);
    console.log('this.lng=', this.lng);
    event.panBy(-(this.winLap.width/2), this.winTrends.height / 1.6)
    console.log('zoom=', event.zoom);

    this.squarePin = {
      path: "M45 1H5v40h15.093l5.439 8.05 5.44-8.05H45z",
      fillColor: '#FFFF33',
      fillOpacity: 1,
      anchor: new google.maps.Point(22,55),
      labelOrigin: new google.maps.Point(24,22),
      strokeWeight: 0.5,
      strokeOpacity: 1,
      scale: 0.65
    };

    this.squarePin2 = {
      path: "M45 1H5v40h15.093l5.439 8.05 5.44-8.05H45z",
      fillColor: '#8A2BE2',
      fillOpacity: 0.5,
      anchor: new google.maps.Point(22,55),
      labelOrigin: new google.maps.Point(24,22),
      strokeWeight: 0.5,
      strokeOpacity: 1,
      scale: 0.65
    };

    // icon for markers
    this.currentIcon= "";

    this.map = event;
    // console.log ('map=',this.map);

    let pos = {
      lat: this.lat,
      lng: this.lng
    }
    let svgIcon = {
      path: google.maps.SymbolPath.CIRCLE,
      scale: 4,
      strokeColor: '#393'
    };

    this.marker = new google.maps.Marker({
        map: this.map,
        position: pos,
        icon: svgIcon
    })
    this.marker.setVisible(false);

  }

  displayTrends() {

    this.padding = { left: 2, top: 2, right: 15, bottom: 5 };
    this.titlePadding = { left: 0, top: 0, right: 0, bottom: 10 };
    this.xAxis =
    {
        valuesOnTicks: true,
        labels:
          {
              formatFunction: (value: any): string => {
                  let hh:number = Math.trunc(value/3600);
                  let mm:number = Math.trunc(value/60)-hh*60;
                  let ss:number = value-hh*3600-mm*60;
                  value = String(hh).padStart(2, '0') + ':' +
                    String(mm).padStart(2, '0') +':' + String(ss).padStart(2, '0');
                  return value;
              },
              angle: 0,
              horizontalAlignment: 'right'
          },
        tickMarks: { visible: true }
    };

    this.seriesGroups =
    [
      {
            type: 'stepline',
            source: this.speedData,
            showToolTips: true,
            toolTipFormatFunction: (value: any, itemIndex: any, serie: any, group: any, categoryValue: any, categoryAxis: any) => {
                let dataItem = this.hrData[itemIndex];
                let pos = {
                        lat: this.w1.gpsCoord[itemIndex].gps_lat,
                        lng: this.w1.gpsCoord[itemIndex].gps_long
                      }
                // console.log('marker: ', pos, this.marker);
                this.marker.setVisible(true);
                this.marker.setPosition(pos);
                this.toolTipTrends = this.getToolTip(itemIndex);
                return '';
             },
            valueAxis:
            {
                title: { text: 'Speed<br>' },
                flip: false,
                labels: { horizontalAlignment: 'right' },
                bands: [],
            },
            series:
            [
                { displayText: 'Speed', lineWidth: 2 }
            ]
        },
        {
            type: 'stepline',
            source: this.hrData,
            showToolTips: true,
            toolTipFormatFunction: (value: any, itemIndex: any, serie: any, group: any, categoryValue: any, categoryAxis: any) => {
                let dataItem = this.hrData[itemIndex];
                let pos = {
                        lat: this.w1.gpsCoord[itemIndex].gps_lat,
                        lng: this.w1.gpsCoord[itemIndex].gps_long
                      }
                // console.log('marker: ', pos, this.marker);
                this.marker.setVisible(true);
                this.marker.setPosition(pos);
                this.toolTipTrends = this.getToolTip(itemIndex);
                return '';
            },
            valueAxis:
            {
                title: { text: 'HeartRate<br>' },
                flip: false,
                labels: { horizontalAlignment: 'right' },
                bands: [],
            },
            series:
            [
                { displayText: 'HeartRate', lineWidth: 2 }
            ]
        },
        {
            type: 'area',
            source: this.elevationData,
            showToolTips: true,
            toolTipFormatFunction: (value: any, itemIndex: any, serie: any, 
              group: any, categoryValue: any, categoryAxis: any) => {
                let dataItem = this.elevationData[itemIndex];
                let pos = {
                        lat: this.w1.gpsCoord[itemIndex].gps_lat,
                        lng: this.w1.gpsCoord[itemIndex].gps_long
                      }
                // console.log('marker: ', pos, this.marker);
                this.marker.setVisible(true);
                this.marker.setPosition(pos);
                this.toolTipTrends = this.getToolTip(itemIndex);
                return '';

            },
            valueAxis:
            {
                title: { text: 'Altitude<br>' },
                flip: false,
                position: 'right',
                labels: { horizontalAlignment: 'right' },
                bands: [],
            },
            series:
            [
                { displayText: 'Altitude', lineWidth: 1, 
                opacity: 0.3  }
            ]
        }
    ];

  }

  getToolTip( index: number ) {
    this.onChartArea = true;
    this.currentIndex = index;
    let coord = this.myChart.getItemCoord(0,0,index);
    this.currentX = coord['x'];
    let averageBand: string='';
    // console.log ('coords=',coord);
    
    if (this.splitBegin >= 0 ) {
      let split: any;
      split = { from: this.splitBegin, to: this.currentX}
      this.recessions[this.currentRecession] = split;
      this.setCurrentBand();

      let lapData = this.getLapInfos(0);
      averageBand = '<b>Split: ' + lapData['strTime'] + '<br />Distance: ' + lapData['dist'] +'</b><br />';
    }
    return '<DIV style="text-align:left">'+averageBand+'<b>Index:</b> ' +
                  index + '<br /><b>HR:</b> ' +
                  this.hrData[index] + '<br /><b>Speed:</b> ' +
                  this.speedData[index] + '<br /><b>Altitude:</b> ' +
                  this.elevationData[index] + '<br /></DIV>';
  }

  showBands () {
    this.bands = [];
    this.Ymin = 0;
    this.Ymax = 0;
    if (this.Ymin == 0) {
      let idx:number = -1;
      for (let i=0; i<this.seriesGroups.length; i++) {
        if (typeof this.seriesGroups[i] !== 'undefined') {
          idx = i;
        }
      }
      if (idx>0) {
        this.Ymin = this.myChart.getValueAxisRect(idx)['y'];
        this.Ymax = <number>this.myChart.getValueAxisRect(idx)['height'];
      }
    }
    for (let i = 0; i < this.recessions.length-1; i++) {
        this.renderer.rect(this.recessions[i].from, 
          this.Ymin, 
          (this.recessions[i].to-this.recessions[i].from), 
          this.Ymax, 
          { fill: '#FFFF33',  opacity: 0.4});
    }
    console.log('showBands recessions=',this.recessions);

  }

  setCurrentBand () {
    let startX: number; 
    console.log('setCurrentBand, currentX= ',this.currentX);
    if ( this.saveCurrentX < 0 && this.splitBegin>=0 )  {
      startX = this.splitBegin;
      console.log('setCurrentBand, first rect');
      this.currentRect = this.renderer.rect(startX, 
        this.myChart.getValueAxisRect(0)['y'], 
        (this.currentX-startX), 
        this.myChart.getValueAxisRect(0)['height'], 
        { fill: '#FFFF33',  opacity: 0.4});

    } else {
      startX = this.saveCurrentX;
      if (this.currentX > this.splitBegin ) {
        this.renderer.attr(this.currentRect, { width:  this.currentX-this.splitBegin});
      }
    }
    this.saveCurrentX = this.currentX;
  }

  updateWatchLapTable (update: number) {
    console.log('>>> updateWatchLapTable');
    this.resetLapsColor();
    this.currentTable = 0;
    if (typeof this.w1.watchLaps != "undefined") {
      this.w1.lap = Object.assign([], this.w1.watchLaps);
      this.lapSize = this.w1.lap.length;
      this.lap_end_index = this.w1.lap[this.lapSize-1].lap_end;
    }
    this.currentIcon = "";
    this.srv.pushWorkout(this.w1.lap, this.selectedTable);
  }

  updateSplitLapTable() {
    console.log('>>> updateSplitLapTable, currentTable=',this.currentTable);
    this.resetLapsColor();
    if ( (this.currentTable==0) ) {
      this.w1.watchLaps = Object.assign([], this.w1.lap);
      console.log('copy watchLaps=',this.w1.watchLaps);
    }
    this.currentTable = 2;
    this.selectedTable = 2;
    this.currentIcon = this.squarePin2;
    this.w1.lap = [];
    this.lap_end_index = 0;
    let k = 1;
    let currentTime = 0;
    let currentDate: Date;

    currentDate = new Date(this.w1.dayTime);
    currentTime = currentDate.getTime()/1000;
    this.done = 0;

    for (let i =0; i< this.w1.splits.length; i++) {
      let l1: Lap = new Lap();

      l1 = {
        lap_index: k++,
        lap_start_index: 0,
        lap_end_index: 0,
        lap_distance: Math.round(this.w1.splits[i].split_distance/1000)*1000,
        lap_time: this.w1.splits[i].split_time,
        lap_start_date: currentDate.toString(),
        lap_cumulatedTime: "00:00:00",
        lap_average_speed: 0,
        lap_average_HR: 0,
        lap_average_cadence: 0,
        lap_pace_zone: 0,
        lap_total_elevation_gain: 0,
        lap_start: 0,
        lap_end: 0
      };
      // console.log ('updateSplitLapTable, split_time=', this.w1.splits[i].split_time);
      let t = new Date('1970-01-01T' + this.w1.splits[i].split_time + 'Z');
      currentTime += t.getTime()/1000;
      currentDate = new Date(currentTime*1000);

      // console.log ('updateSplitLapTable, lap_start_date=', currentTime, currentDate.toString());
      this.w1.lap.push(l1);
    }

    if ( this.w1.splits.length ) {

      this.computeWatchLapIndex(0,1);
      this.lapSize = this.w1.lap.length;
      this.lap_end_index = this.w1.lap[this.lapSize-1].lap_end;
      this.w1.lap.sort(this.compare);
      
      console.log ('updateSplitLapTable, w1.lap=', this.w1.lap);

      for (let i =0; i< this.w1.lap.length; i++) {
        let avgSpeed: number = 0;
        let avgHR: number = 0;
        for (let j=this.w1.lap[i].lap_start; j<=this.w1.lap[i].lap_end;j++) {
          avgSpeed+=this.speedData[j];
          avgHR+=this.hrData[j];
        }
        avgSpeed=avgSpeed/(this.w1.lap[i].lap_end-this.w1.lap[i].lap_start+1);
        avgSpeed = Math.trunc(avgSpeed*100)/100;
        avgHR=avgHR/(this.w1.lap[i].lap_end-this.w1.lap[i].lap_start+1);
        avgHR = Math.trunc(avgHR);
        // console.log('avgSpeed1=',avgSpeed);
        this.w1.lap[i].lap_average_speed = avgSpeed;
        this.w1.lap[i].lap_average_HR = Math.round(avgHR);
       }

    }

    this.done = 1;

    this.srv.pushWorkout(this.w1.lap,this.selectedTable);
  }

  updateCustomLapTable () {
    console.log('>>> updateCustomLapTable, currentTable=',this.currentTable);
    this.resetLapsColor();

    if ( (this.currentTable==0) ) {
      this.w1.watchLaps = Object.assign([], this.w1.lap);
      console.log('copy watchLaps=',this.w1.watchLaps);
    }
    this.currentTable = 1;
    this.selectedTable = 1;
    this.currentIcon = this.squarePin;
    this.w1.lap = [];
    this.lap_end_index = 0;
    let k = 1;
    let beginTime: number = this.startHour;
    for (let i = this.recessions.length-1; i >0 ; i--) {
      let lapData = this.getLapInfos (i);
      let l1: Lap = new Lap();
      let avgSpeed: number = 0;
      let avgHR: number = 0;
      for (let i=lapData['idx1']; i<=lapData['idx2'];i++) {
        avgSpeed+=this.speedData[i];
        avgHR+=this.hrData[i];
      }
      avgSpeed=avgSpeed/(lapData['idx2']-lapData['idx1']+1);
      avgSpeed = Math.trunc(avgSpeed*100)/100;
      avgHR=Math.round(avgHR/(lapData['idx2']-lapData['idx1']+1));
      console.log('avgSpeed1=',avgSpeed);
      l1 = {
        lap_index: k++,
        lap_start_index: lapData['idx1'],
        lap_end_index: 0,
        lap_distance: lapData['dist'],
        lap_time: lapData['strTime'],
        lap_start_date: (beginTime+lapData['startTime']).toString(),
        lap_cumulatedTime: "00:00:00",
        lap_average_speed: avgSpeed,
        lap_average_HR: avgHR,
        lap_average_cadence: 0,
        lap_pace_zone: 0,
        lap_total_elevation_gain: 0,
        lap_start: lapData['idx1'],
        lap_end:lapData['idx2']
      };
      console.log('splitLap=',l1, 'lap_start_date=',l1.lap_start_date);
      this.w1.lap.push(l1);
      this.lapSize = this.w1.lap.length;
      this.lap_end_index = this.w1.lap[this.lapSize-1].lap_end_index;
      this.w1.lap.sort(this.compare);
      k = 1;
      this.w1.lap.forEach(element => {element['lap_index']=k++;});
      console.log ('updateCustomLapTable, w1.lap=', this.w1.lap);

     }
     this.srv.pushWorkout(this.w1.lap,this.selectedTable);
  }

  compare (a: Lap, b: Lap) {
    let comparison = 0;
    let t1 = a.lap_start_date;
    let t2 = b.lap_start_date;

    if ( t1 > t2 ) comparison = 1;
    if ( t1 < t2 ) comparison = -1;

    return comparison;
  }

  convertAbstoIndex (x:number) {
    let w:string|number = <number>this.myChart.getXAxisRect(0)['width'];
    let index:number = (x-this.myChart.getXAxisRect(0)['x'])*this.w1.gpsCoord.length/w;
    // console.log('index=',index);
    return ( Math.round(index) );
  }

  draw = (renderer: any, rect: any): void => {
    this.renderer = renderer;
    this.rect = rect;
  };

  getLapInfos (idx: number) {
    let idx1:number = this.convertAbstoIndex(this.recessions[idx].from);
    let idx2:number = this.convertAbstoIndex(this.recessions[idx].to);
    console.log ('getLapInfos, idx1=', idx1, 'idx2=',idx2);
    let t = this.w1.gpsCoord[idx2].gps_time - this.w1.gpsCoord[idx1].gps_time;
    let hh:number = Math.trunc(t/3600);
    let mm:number = Math.trunc(t/60)-hh*60;
    let ss:number = t-hh*3600-mm*60;
    let averageTime = String(hh).padStart(2, '0') + ':' +
      String(mm).padStart(2, '0') +':' + String(ss).padStart(2, '0');
    let dist:number = Math.round(this.distanceData[idx2] - this.distanceData[idx1]);
    return {idx1: idx1, idx2: idx2, dist: dist, strTime: averageTime, startTime: idx1};
  }

  ngAfterViewInit() {
    console.log("ngAfterViewInit");
    this.mapsAPILoader.load().then(() => {
      console.log("load Agm");
    });
  }

  binaryIndexOf(searchElement, correction) {
    'use strict';
 
    var minIndex = 0;
    var maxIndex = this.resolution - 1;
    var accuracy;
    if (correction) {
      accuracy = this.workoutSize/this.resolution;
    } else {
      accuracy = 1;
    }
    // console.log('workoutSize=',this.workoutSize,'accuracy=',accuracy);
    var currentIndex;
    var currentElement;
    // console.log ('binaryIndexOf, searchElement=', searchElement);
    while (minIndex <= maxIndex) {
        currentIndex = (minIndex + maxIndex) / 2 | 0;
        // console.log ('binaryIndexOf, currentIndex=', currentIndex);
        currentElement = this.w1.gpsCoord[currentIndex].gps_time;
 
        if ( (currentElement < searchElement) && 
             (Math.abs(currentElement-searchElement)>accuracy) ) {
            minIndex = currentIndex + 1;
        }
        else if ( (currentElement > searchElement) && 
                  (Math.abs(currentElement-searchElement)>accuracy) ) {
            maxIndex = currentIndex - 1;
        }
        else {
            let delta=(currentElement-searchElement);
            let index: number = currentIndex;
            // console.log('delta=',delta);
            if ( delta>0 && Math.abs(delta)>(accuracy/2) ) {
              // console.log('correction -1');
              index =  currentIndex-1;
            }
            if ( delta<0 && Math.abs(delta)>(accuracy/2) ) {
              // console.log('correction +1');
              index = currentIndex+1;
            }
            // console.log('index=',index, 'res=', this.resolution);
            if ( index > (this.resolution - 1) ) {
              index = this.resolution - 1;
            }
            // console.log('return index=',index);
            return index;
        }
    }
 
    return -1;
  }

  resetLapsColor () {
    console.log ('resetLapsColor, resolution=',this.resolution);
    for (let i=0;i<this.resolution;i++) {
      this.w1.gpsCoord[i].strokeWeight = 2;
      this.w1.gpsCoord[i].color = '#2196f3';
    }
  }


  onLapSelected (lap: lapSelection) {
    // console.log(">>>> onLapSelected, lap=", numLap);
    let strokeWeight:number;
    let color:string;
    let numLap=lap.lap_idx;
    if (lap.lap_idx > 0) {
      strokeWeight = 4;
      if (lap.isCurrent) {
        color = 'black';
      } else {
        switch(this.selectedTable) { 
           case 0: { 
              color = 'red';
              break; 
           } 
           case 1: { 
              color = 'yellow';
              break; 
           }
           case 2: { 
              color = '  #8A2BE2';
              break; 
           }  
           default: { 
              color = 'red';
              break; 
           } 
         } 
      }
    } else {
      numLap= lap.lap_idx * (-1);
      strokeWeight = 2;
      color = '#2196f3';
    }
    numLap = numLap -1;
    let i:number=0;
    
    let start_idx = this.w1.lap[numLap].lap_start;
    let end_idx = this.w1.lap[numLap].lap_end;
    // console.log(">>>> onLapSelected, speed=",speed);
    for(i = start_idx;i<end_idx;i++) {
      this.w1.gpsCoord[i].strokeWeight = strokeWeight;
      this.w1.gpsCoord[i].color = color;
      // console.log(">>>> onLapSelected, i=",i,"speed=",this.w1.gpsCoord[i].speed);
    }
  }

  onTableSelect (event: any) {
    console.log('onTableSelect, selection: ',this.selectedTable);
    switch(this.selectedTable) { 
     case 0: { 
        this.updateWatchLapTable (1);
        break; 
     } 
     case 1: { 
        this.updateCustomLapTable (); 
        break; 
     }
     case 2: { 
        this.updateSplitLapTable (); 
        break; 
     }  
     default: { 
        break; 
     } 
   }

  }

  onLapInfos(data: infos) {
    // console.log(">>>> onLapInfos, total dist=",data.total_dist, 
    //  "average time=",data.average_time,
    //  "nbValues=",data.nbValues);

    if ( data.nbValues > 1) {
      this.lapInfos.show = true;
    }  else {
      this.lapInfos.show = false;
    }
    this.infosData[0]['value'] = data.total_time;
    this.infosData[1]['value'] = data.average_time;
    this.infosData[2]['value'] = data.average_speed;
    this.infosData[3]['value'] = String(data.total_dist);
    // console.log(">>>> onLapInfos, infosData=",this.infosData);
  }

  clickedMarker(label: string, index: number) {
    console.log('clicked the marker:', index);
    let idx:number = index-1;
    if (idx>=0 || (this.selectedTable==1)) {
      if (this.selectedTable==1) {
        idx = idx + 1;
      }
      this.clickLapDistance = this.w1.lap[idx].lap_distance;
      this.clickLapTime = this.w1.lap[idx].lap_time.toString();
    } else {
      this.clickLapDistance = 0;
      this.clickLapTime = "00:00:00";  
    }
  }

  onClickSettings () {
    console.log('clicked Settings button');
    this.showSettings = !this.showSettings;
  }

  onChartEvent(event: any): any {
        let eventData;
        // console.log('chartEvent: ',event.type);
        if (event) {
            if (event.args) {
                if (event.type == 'toggle') {
                  this.splitBegin = -1;
                  this.saveCurrentX = -1;
                  this.onChartArea = false;
                  this.timer = setTimeout(() => {
                    this.showBands();
                  }, 500);  
                }
            } else if (event.type == 'mouseleave') {
                  this.marker.setVisible(false);
                  this.splitBegin = -1;
                  this.saveCurrentX = -1;
                  this.onChartArea = false;
             } else if (event.type == 'mousedown') {
                  if (this.splitBegin <0 ) {
                    this.splitBegin = this.currentX;
                    this.currentRecession = this.bands.length;
                    console.log ('splitBegin=',this.splitBegin);
                  } 
            } else if (event.type == 'mouseup') {
                  if ( (this.splitBegin != this.currentX)  && (this.currentX - this.splitBegin)>0 )  {
                    let split: any;
                    split = { from: this.splitBegin, to: this.currentX }
                    if( this.recessions.indexOf(split) === -1)  {
                      console.log ('push split', split);
                      this.recessions.push(split);
                      this.updateCustomLapTable();
                    }
                    this.splitBegin = -1;
                    this.saveCurrentX = -1;
                    console.log ('recessions=',this.recessions);
                  } else {
                    this.splitBegin = -1;
                    this.saveCurrentX = -1;
                  }
            }
        }
  }

  @HostListener('document:mousemove', ['$event'])
  onCornerMove(event: MouseEvent) {
    if (!this.selectedWindow.draggingCorner) {
      return;
    }
    let offsetX = event.clientX - this.selectedWindow.px;
    let offsetY = event.clientY - this.selectedWindow.py;

    let lastX = this.selectedWindow.x;
    let lastY = this.selectedWindow.y;
    let pWidth = this.selectedWindow.width;
    let pHeight = this.selectedWindow.height;

    this.selectedWindow.resizer(offsetX, offsetY);
    if (this.selectedWindow.area() < this.selectedWindow.minArea) {
      this.selectedWindow.x = lastX;
      this.selectedWindow.y = lastY;
      this.selectedWindow.width = pWidth;
      this.selectedWindow.height = pHeight;
    }
    this.selectedWindow.px = event.clientX;
    this.selectedWindow.py = event.clientY;
  }

  @HostListener('document:mouseup', ['$event'])
  onCornerRelease(event: MouseEvent) {
    this.selectedWindow.draggingWindow = false;
    this.selectedWindow.draggingCorner = false;
    if (this.redrawBands)
      this.showBands();
  }

  @HostListener('window:resize', ['$event'])
  onResize(event) {
    this.newInnerHeight = event.target.innerHeight;
    this.newInnerWidth = event.target.innerWidth;
    this.updateView();
    /* this.fitToScreen(this.agmMap); */
  }
}

export interface LapTable {
  value: number;
  viewValue: string;
}

export interface infoTable {
  title: string;
  value: string;
}

export class infos {
  total_dist: number;
  total_time: string;
  average_time: string;
  average_speed: string;
  nbValues: number;
  show: boolean;
}


export class Window {
  name: string;
  app: AppComponent;
  x: number;
  y: number;
  px: number;
  py: number;
  width: number;
  height: number;
  draggingCorner: boolean;
  draggingWindow: boolean;
  minArea: number;
  resizer: Function;

  constructor(private father: AppComponent) {
    this.app = father;
  }

  area() {
    return this.width * this.height;
  }

  onWindowPress(event: MouseEvent, id: number) {
    if (!this.app.onChartArea) {
      this.app.selectedWindow = this;
      this.draggingWindow = true;
      this.px = event.clientX;
      this.py = event.clientY;
      console.log('Press winId=', id);
    }
  }

  onWindowDrag(event: MouseEvent, id: number) {
    if (!this.draggingWindow) {
      return;
    }
    let offsetX = event.clientX - this.px;
    let offsetY = event.clientY - this.py;

    this.x += offsetX;
    this.y += offsetY;
    this.px = event.clientX;
    this.py = event.clientY;

    this.father.redrawBands = false;
  }

  onWindowEnter(event: MouseEvent, id: number) {
    console.log ('>>> onWindowEnter : ', id);
    this.app.selectedWindow = this;
  }

  topLeftResize(offsetX: number, offsetY: number) {
    this.x += offsetX;
    this.y += offsetY;
    this.width -= offsetX;
    this.height -= offsetY;
    this.father.redrawBands = true;
  }

  topRightResize(offsetX: number, offsetY: number) {
    this.y += offsetY;
    this.width += offsetX;
    this.height -= offsetY;
    this.father.redrawBands = true;
  }

  bottomLeftResize(offsetX: number, offsetY: number) {
    this.x += offsetX;
    this.width -= offsetX;
    this.height += offsetY;
    this.father.redrawBands = true;
  }

  bottomRightResize(offsetX: number, offsetY: number) {
    this.width += offsetX;
    this.height += offsetY;
    this.father.redrawBands = true;
  }

  onCornerClick(event: MouseEvent, resizer?: Function) {
    this.draggingCorner = true;
    this.px = event.clientX;
    this.py = event.clientY;
    this.resizer = resizer;
    event.preventDefault();
    event.stopPropagation();
  }
}

