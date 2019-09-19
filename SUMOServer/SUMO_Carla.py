#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import time
import socket
import lcm
import argparse
from npc_control import Waypoint, action_result, connect_request, connect_response, action_package, end_connection, suspend_simulation
from xml_reader import XML_Tree
from collections import deque

const_speed = 0x40
const_position = 0x42
const_2d_position = 0x00
const_angle = 0x43

const_road_id = 0x50
const_lane_id = 0x51

const_route_id = 0x53
const_edge_id = 0x54
const_lane_position = 0x56
const_best_lanes = 0xb2

file_route_id_prefix = "file_route_"
new_route_id_prefix = "manual_route_"
vehicle_id_prefix = "manual_vehicle_"

connect_request_keyword = "connect_request"
connect_response_keyword = "connect_response"
action_result_keyword = "action_result"
action_package_keyword = "action_package"
end_connection_keyword = "end_connection"
suspend_simulation_keyword = "suspend_simulation"

basic_vehicle_info = (const_2d_position, const_route_id, const_edge_id, const_lane_id)

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    print("current SUMO Path is " + tools)
    sys.path.append(tools)
    print('sumo path set done')
else:
    sys.exit("please declare environmentvariable 'SUMO_HOME'")



import traci
import traci.constants as tc
import random

print("traci import done")


class Vehicle_Client:
    def __init__(self, veh_id, rou_id):
        self.vehicle_id = veh_id
        self.route_id = rou_id
        self.simulation_steps = 0
        self.expected_simulation_steps = 0
        self.waypoint_queue = deque(maxlen=100)


class traci_simulator:
    def __init__(self, cfg_path):
        sim_rou_path = cfg_path.split('.')[0] + '.rou.xml'
        sim_net_path = cfg_path.split('.')[0] + '.net.xml'
        self.config_file_path = cfg_path
        self.sumoBinary = 'sumo'
        self.sumocmd = [self.sumoBinary, "-c", self.config_file_path]
        self.vehicle_ids = []
        rou_xml_tree = XML_Tree(sim_rou_path)
        net_xml_tree = XML_Tree(sim_net_path)
        self.routes = rou_xml_tree.read_routes()
        # new route count
        self.manual_route_num = 0
        # route count from .rou.xml file.
        self.file_route_num = 0
        self.offsets = net_xml_tree.read_offset()
        self.message_waypoints_num = 3
        self.lc = lcm.LCM()
        # 用id-vehicle对来存储所有客户端
        self.vehicle_clients = {}
        # 监听需要接收的消息
        self.lc.subscribe(connect_request_keyword, self.connect_request_handler)
        self.lc.subscribe(action_result_keyword, self.action_result_handler)
        self.lc.subscribe(suspend_simulation_keyword, self.suspend_simualtion_handler)


    """
    transform from LCM waypoint to TraCi waypoint which will be used here
    """

    def transform_LCM_to_SUMO_Waypoint(self, waypoint):
        res_point = (
            waypoint.Location[0] + self.offsets[0],
            waypoint.Location[1] + self.offsets[1]
        )
        return res_point

    """
    transform from Traci waypoint to LCM waypoint which will be used in Carla
    """

    def transform_SUMO_to_LCM_Waypoint(self, waypoint, height, angle):
        lcm_waypoint = Waypoint()
        lcm_waypoint.Location = [
            waypoint[0] - self.offsets[0],
            waypoint[1] - self.offsets[1],
            height
        ]
        lcm_waypoint.Rotation = [0.0, angle, 0.0]
        return lcm_waypoint

    def get_LCM_Waypoint(self, id):
        try:
            traci_point = traci.vehicle.getPosition(id)
            # print(traci_point)
            height = traci.vehicle.getHeight(id)
            traci_angle = traci.vehicle.getAngle(id)
            # print("angle: ", traci_angle)
            lcm_waypoint = Waypoint()

            lcm_waypoint.Location = [
                traci_point[0] - self.offsets[0],
                traci_point[1] - self.offsets[1],
                height
            ]
            lcm_waypoint.Rotation = [0.0, traci_angle, 0.0]
            return lcm_waypoint
        except traci.exceptions.TraCIException:
            # print("traci exception during getting vehicle info")
            return None
        except Exception:
            print("other error happened")
            return None

    # function called to select a random edge from file routes.
    def select_random_end_edge(self):
        rou_index = random.randint(0, self.file_route_num - 1)
        rou_id = file_route_id_prefix + str(rou_index)
        edges_list = traci.route.getEdges(rou_id)
        print("edge list: ", edges_list)
        return edges_list[len(edges_list) - 1]

    # generate a new vehicle id 
    def get_new_vehicle_id(self):
        if self.vehicle_ids.count == 0:
            new_id = vehicle_id_prefix + "0"
            self.vehicle_ids.append(new_id)
            return new_id
        else:
            maxid = -1
            for id in self.vehicle_ids:
                id_num = int(id.split('_')[2])
                if id_num > maxid:
                    maxid = id_num
            new_id = vehicle_id_prefix + str(maxid + 1)
            self.vehicle_ids.append(new_id)
            return new_id

    # function called to create a new vehichle in SUMO Server.
    # 

    def new_vehicle_event(self):

        # print("initial position of the new vehicle: ", init_pos)
        # convert_res = traci.simulation.convertRoad()
        # print("traci.simulation.convertRoad result: ", convert_res)

        # start_edge = traci.simulation.convertRoad(init_pos[0], init_pos[1])[0]
        # end_edge = self.select_random_end_edge()
        # print("start edge: ", start_edge, ", end edge: ", end_edge)
        # find_route_res = traci.simulation.findRoute(start_edge, end_edge)
        # edges_list = find_route_res.edges
        # print("edges list: ", edges_list)
        # rou_name = new_route_id_prefix + str(self.manual_route_num)
        # self.manual_route_num += 1
        # print("rou name: ", rou_name)
        # traci.route.add(rou_name, edges_list)
        # traci.vehicle.add(new_id, rou_name)
        # 构造connect_response消息并发送
        # msg = connect_response()
        # msg.vehicle_id = new_id
        # self.lc.publish(connect_response_keyword, msg.encode())
        # print("publish done. vehicle id: ", new_id)

        new_id = self.get_new_vehicle_id()
        print('new id for the client: ', new_id)
        # 从所有预设路线的前一半中随机选取一个作为初始路线
        # 尝试解决非法路线的问题
        rou_cnt = int(traci.route.getIDCount())
        print("rou count: ", rou_cnt)
        veh_rou_id = file_route_id_prefix + str(random.randint(0, rou_cnt - 1))
        print('route id for the client: ', veh_rou_id)
        # # add vehicle过程中可能出现invalid route的Exception，故不断重新选择路线进行尝试直到不抛异常
        while True:
            try:
                traci.vehicle.add(new_id, veh_rou_id)
            except Exception:
                # 重新选择路线
                veh_rou_id = file_route_id_prefix + str(random.randint(0, rou_cnt - 1))
                continue
            break
        new_vehicle = Vehicle_Client(new_id, veh_rou_id)
        self.vehicle_clients[new_id] = new_vehicle
        # # traci.vehicle.subscribe(new_id, [const_2d_position])
        traci.simulationStep()
        traci.simulationStep()
        # init_pos = traci.vehicle.getSubscriptionResults(new_id)[const_position]
        # # print("demo pos: ", traci.vehicle.getPosition(new_id))
        # print("init pos: ", init_pos)
        # 构造connect_response消息并发送
        msg = connect_response()
        msg.vehicle_id = new_id
        init_pos_way = self.get_LCM_Waypoint(new_id)
        while init_pos_way.Location[0] > 10000:
            traci.simulationStep()
            init_pos_way = self.get_LCM_Waypoint(new_id)
        msg.init_pos = init_pos_way
        self.lc.publish(connect_response_keyword, msg.encode())
        print("publish done. vehicle id: ", new_id)
        return new_id

    # 有客户端发来连接请求，添加车辆并进行仿真
    def connect_request_handler(self, channel, data):
        print("Received message on channel ", channel)
        msg = connect_request.decode(data)
        id = self.new_vehicle_event()
        next_action = action_package()
        for i in range(self.message_waypoints_num):
            # traci.simulationStep()
            self.simulation_step(id)
            next_action.waypoints[i] = self.get_LCM_Waypoint(id)
            # print("#",i, " position: ", traci.vehicle.getPosition(id))
        # traci.simulationStep()
        # traci.simulationStep()
        # print("current position: ", traci.vehicle.getPosition(id))
        # 服务器端仿真完成，发送后续路点给客户端

        next_action.vehicle_id = id
        # next_action.waypoints[0] = self.transform_SUMO_to_LCM_Waypoint(id)
        # next_action.target_speed = traci.vehicle.getSpeed(id)
        self.lc.publish(action_package_keyword, next_action.encode())
        print("action package publish done!")

    # 有客户端发来行驶结果，等待所有车辆发来结果或到达最大等待时间后进行下一步仿真
    # 根据车辆id设置相应的车辆的实际状态
    def action_result_handler(self, channel, data):
        print("Received message on channel ", channel)
        msg = action_result.decode(data)
        # print("action result position: ", msg.current_pos.Location)
        res_position = self.transform_LCM_to_SUMO_Waypoint(msg.current_pos)
        try:
            print("action result position: ", res_position)
            # print("current position in SUMO: ", traci.vehicle.getPosition(msg.vehicle_id))
            print("action result vehicle id: ", msg.vehicle_id)
            lane = traci.vehicle.getLaneIndex(msg.vehicle_id)
            edge = traci.vehicle.getRoadID(msg.vehicle_id)
            edge = edge.split(".")[0]
            print("traci edge: ", edge)
            # print("traci lane: ", lane)
            # print("lane: ", int(lane), ", edge: ", int(edge))
        except traci.exceptions.TraCIException:
            print("vehicle simulation ended.")
            end_pack = end_connection()
            end_pack.vehicle_id = msg.vehicle_id
            self.lc.publish(end_connection_keyword, end_pack.encode())
            return
        # except Exception:
        #     print("server fatal error")
        #     return
        try:
            # pass
            traci.vehicle.moveToXY(msg.vehicle_id, edge, lane, res_position[0], res_position[1], keepRoute=1)
        except traci.exceptions.FatalTraCIError:
            print("traci fatal error caught")
            return
        print("position after movetoxy(): ", traci.vehicle.getPosition(msg.vehicle_id))
        # 如果当前是停车状态，则恢复行驶
        # if traci.vehicle.isStopped(msg.vehicle_id):
        #     traci.vehicle.resume(msg.vehicle_id)
        # if traci.vehicle.getSpeed(msg.vehicle_id) <= 1.0:
        #     traci.vehicle.slowDown(msg.vehicle_id, 20.0, 10000)
        next_action = action_package()
        for i in range(self.message_waypoints_num):
            # if len(self.vehicle_clients[msg.vehicle_id].waypoint_queue) > 0:
            #     temp_point = self.vehicle_clients[msg.vehicle_id].waypoint_queue.popleft()
            #     next_action.waypoints[i] = temp_point
            # # traci.simulationStep()
            # else:
            #     # traci.simulationStep()
            #     self.simulation_step(msg.vehicle_id)
            #     temp_point = self.get_LCM_Waypoint(msg.vehicle_id)
            #     next_action.waypoints[i] = temp_point
            # try:
            #     traci.simulationStep()
            # except traci.exceptions.FatalTraCIError:
            #     print("traci fatal error during simulation step")
            #     return
            traci.simulationStep()
            traci.simulationStep()
            temp_point = self.get_LCM_Waypoint(msg.vehicle_id)
            next_action.waypoints[i] = temp_point
            if temp_point is None:
                print("vehicle simulation ended.")
                end_pack = end_connection()
                end_pack.vehicle_id = msg.vehicle_id
                self.lc.publish(end_connection_keyword, end_pack.encode())
                return
        # 服务器端仿真完成，发送后续路点给客户端
        next_action.vehicle_id = msg.vehicle_id
        # next_action.waypoints[0] = self.transform_SUMO_to_LCM_Waypoint(msg.vehicle_id)
        # next_action.target_speed = traci.vehicle.getSpeed(msg.vehicle_id)
        self.lc.publish(action_package_keyword, next_action.encode())
        print("action package publish done!")

    def suspend_simualtion_handler(self, channel, data):
        print("Received message on channel ", channel)
        msg = suspend_simulation.decode(data)
        current_pos = self.transform_LCM_to_SUMO_Waypoint(msg.current_pos)
        print("id ", msg.vehicle_id, ": suspend simulation. current pos: ", current_pos)
        try:
            lane = traci.vehicle.getLaneIndex(msg.vehicle_id)
            edge = traci.vehicle.getRoadID(msg.vehicle_id)
            edge = edge.split(".")[0]
            traci.vehicle.moveToXY(msg.vehicle_id, edge, lane, current_pos[0], current_pos[1], keepRoute=1)
        except traci.exceptions.TraCIException:
            print("traci exception. ")


    def simulation_step(self, veh_id):
        try:
            traci.simulationStep()
            traci.simulationStep()
        except traci.exceptions.FatalTraCIError:
            print("caught fatal traci error during simulation step!")
            return
        for (key, value) in self.vehicle_clients.items():
            value.simulation_steps += 1
            if key != veh_id:
                new_pos = self.get_LCM_Waypoint(key)
                value.waypoint_queue.append(new_pos)

    def main_loop(self):
        traci.start(self.sumocmd)
        # no need to add routes from file.
        i = 0
        for route in self.routes:
            route_name = file_route_id_prefix + str(i)
            traci.route.add(route_name, route)
            # print(traci.route.getEdges(route_name))
            i += 1
            self.file_route_num += 1
        print("begin listening LCM messages...")
        # print("find_route result: ", type(find_route_res))
        # print("traci simulation test type: ", type(traci.simulation.convertRoad(0.0, 0.0)))
        while True:
            try:
                self.lc.handle()
            except KeyboardInterrupt:
                sys.exit()
                return
        # while True:
        #     self.lc.handle()


def main():
    argparser = argparse.ArgumentParser(
        description='SUMO Simulation Client')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-S', '--source',
        default='simulations/Town03/Town03.sumocfg',
        help='source of the sumo config file',
    )
    args = argparser.parse_args()
    # sim_path = args.source.split('.')[0] + '.rou.xml'

    # print(sim_path)
    # print(args.source)
    simulator = traci_simulator(args.source)
    # simulator.start_simulation()
    simulator.main_loop()


if __name__ == "__main__":
    main()
