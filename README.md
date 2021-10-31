# TiEV - Traffic Flow Injection Co-simulation Program

## 1 Overview

​ In order to improve the authenticity of the background traffic flow in the driverless simulation scene, this project implements a joint simulation program between the driverless simulation platform CARLA and the microscopic traffic flow simulation system SUMO, and injects the background traffic flow in SUMO into the CARLA scene And perform synchronous simulation.


## 2  Traffic flow injection method based on indirect control of vehicles

### 2.1 Overview

​	The method in this section is the method proposed at the beginning of the project. Since the co-simulation system does not directly control the vehicle in the simulation scene, it is called an injection method for indirect control of the vehicle. Considering that this type of method is completely based on the vehicle client implementation, the supported traffic flow injection scale is small.

### 2.2 Example result

![result](images/TiEV/CARLA_Automatic.gif)

### 2.3 Instructions for use

``` shell
# Run the 0.9.8 version of CARLA server program
$ ./CarlaUE4.sh
# Run traffic server program
$ python SUMOServer/SUMO_Carla.py 
# Running background car client, according to need to run several
$ python Co-Simulation/background_client.py 
```



## 3 Traffic flow injection method based on directly controlling vehicles

### 3.1 Overview

​	​ CARLA officially added support for SUMO co-simulation in the version 0.9.8 of CARLA released in March 2020. The core idea of ​​the official implementation method is to control all vehicles in the scene directly from the level of the simulation scene without going through the vehicle client. The traffic flow scale supported by this method is very large (but also limited by server-side performance), but it does not support client-level control methods.

### 3.2 Example

![](images/TiEV/Direct_Injection.gif)

### 3.3 Instructions for use

``` shell
# Run the 0.9.8 version of CARLA server program, not in the current directory
$ ./CarlaUE4.sh
# Windows environment runs the traffic flow injection program
$ ./Co-Simulation/injection.bat

```



## 4 Traffic flow injection method based on hybrid control vehicles

### 4.1 Overview

​ The hybrid control method here essentially integrates the vehicle control method of the direct control method and the two-terminal interaction framework of the indirect control method to realize the control support at the client level to simulate the control required by some clients Typical scenario.

### 4.2 Result

​	Shown here is a manual control vehicle embedded in a hybrid control frame to avoid the background traffic in front of it.

![](images/TiEV/Mixed_Injection.gif)

​	Currently, the background car client directly controlled by the traffic flow server in the hybrid control method still has the problem of instability, and because this type of vehicle is also regarded by the traffic flow server as a car controlled by CARLA, it will be in the same vehicle. The location automatically generates duplicate vehicles, as shown in the figure below.

![](images\TiEV\Hybrid_Coupling.png)

​ Therefore, this problem needs to be optimized and resolved.

### 4.3 Instructions for use

``` shell
# Run the 0.9.8 version of CARLA server program, not in the current directory
$ ./CarlaUE4.sh
# Windows environment to run the traffic flow server (based on the direct method of injection program construction)
$ ./Co-Simulation/injection.bat
#Run the background car client directly controlled by the traffic flow server
$ python Co-Simulation/client_main.py
# Manual operation of embedded control client interaction framework
$ python Co-Simulation/client_main.py --is-manual=True
# Manual control client requests Press V escape ahead of the vehicle
```



## 5 Other

### 5.1 Automatically generate SUMO simulation files based on OpenDrive road network files

​	We built script programs that input OpenDrive files and output simulation files such as .sumocfg, .trip.xml, etc. The program specifically builds visible SUMOServer/generate_simulation.shfiles. This script program can only be run under Unix environment at present, and it can be rewritten into a Windows script file in .bat format later.

​ However, the current problem in this part is that the automatically generated journey file `.trip.xml` often cannot cover all the roads in the scene during the actual simulation process. Regarding this issue, I found the relevant statement from the randomTrips.pyofficial document `randomTrips.py` : [randomTrips.py](https://sumo.dlr.de/docs/Tools/Trip.html)

> This task is performed by the router. If the network is not fully connected some of the trips may be discarded.

​ Therefore, this part needs further testing.
