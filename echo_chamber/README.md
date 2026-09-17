# Week 0: Setting the Foundation & The First Node

Welcome to Week 0 of the course! Before we can make robots move autonomously, we need to set up our digital workshop. This week is all about installing the right tools, understanding how to organize your code, mastering the command line, and writing your very first ROS 2 nodes.

## 1. Environment Setup

To ensure everyone is developing in the exact same environment, we will be using the following software stack. Please follow the official installation guides linked below.

* **Operating System:** Ubuntu 22.04 LTS (Refer the handout for Dual Boot/VM setup)
* **ROS 2 Distribution:** ROS 2 Humble ([Desktop Install](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html))
* **Simulator:** Gazebo Fortress ([follow the documentation for installation](https://gazebosim.org/docs/fortress/install_ubuntu/))

---

## 2. Workspace & GitHub Setup

We will be organizing all of our code into a single ROS 2 workspace. For this course, your workspace will be named `qstp_ws`.

### Creating the Workspace
Open a terminal and run the following commands to create your workspace and the `src` directory where all your packages will live:

```bash
mkdir -p ~/qstp_ws/src
cd ~/qstp_ws
```

### Setting up Version Control

We will use GitHub for all assignment submissions. To ensure your local code syncs properly with GitHub, follow these exact steps:

#### Step 1: Create the Remote Repository

1. Go to [GitHub](https://github.com) and log into your account.

2. Click the New repository button.

3. Name the repository exactly ERC_ROS2_QSTP_26 

4. Set the repository visibility to Public.

5. Do not check the boxes to add a README, .gitignore, or License. You need the repository to be completely empty.

6. Click Create repository.

#### Step 2: Initialize the Local Repository

Now, open your terminal and initialize Git inside your local src folder. This tracks your custom packages and links your local folder to the GitHub repository you just created.

```bash
cd ~/qstp_ws/src
git init
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/ERC_ROS2_QSTP_26.git
``` 

**Replace <YOUR_GITHUB_USERNAME> with your actual GitHub ID**

Your final folder structure for the course should look like this:

```text
qstp_ws/
├── src/                   <-- Your Git repository lives here!
│   ├── echo_chamber/      <-- Your package for this week
│   ├── week1_assignment/
│   └── ...
├── (build, install, and log folders stay safely outside your repo)
└── README.md              <-- To document your work throughout the duration of this course
```

---

## 3. The ROS 2 CLI Cheat Sheet

The Command Line Interface (CLI) is your best friend in ROS 2. You will use these commands constantly to debug and inspect your robot's systems.

### Node & Package Commands

* `ros2 pkg create --build-type ament_python <package_name>` - Creates a new Python-based ROS 2 package.

* `ros2 run <package_name> <executable_name>` - Runs a specific node.

* `ros2 node list` - Shows all currently running nodes.

* `ros2 node info <node_name>` - Shows detailed information about a specific node (its publishers, subscribers, services, etc.).

### Workspace Commands

* `colcon build` - Compiles all the packages in your workspace. (Always run this from the root ~/qstp_ws directory).

* `colcon build --packages-select <package_name>` - Builds only a specific package.

* `source install/setup.bash` - Sources your built workspace so ROS 2 can find your custom executables 

### Topic Commands

* `ros2 topic list` - Lists all active topics in the ROS 2 graph.

* `ros2 topic echo <topic_name>` - Prints the data being published to a topic in real-time.

* `ros2 topic hz <topic_name>` - Shows the publishing frequency (Hertz) of a topic.

---

## 4. Assignment: "The Echo Chamber"

### Objective:

Create your first custom ROS 2 package containing two Python nodes: a Publisher and a Subscriber. This will help you get familiar with rclpy boilerplate code, spinning nodes, and logging information to the terminal.

### Step 1: Create the Package

Navigate to your src directory and create a new Python package named week0_basics.

```bash
cd ~/qstp_ws/src
ros2 pkg create --build-type ament_python echo_chamber --dependencies rclpy std_msgs
```

Make sure to add this `README.md` file inside your echo_chamber folder

### Step 2: The Publisher Node (talker.py)

Create a Python script in your package that does the following:

* Inherits from the Node class.

* Creates a publisher on a topic named /random_number using the std_msgs/msg/Float32 message type.

* Uses a timer to publish a random float between 0.0 and 100.0 every 1 second (1.0 Hz).

* Uses self.get_logger().info() to print the number it just published to the terminal.

* Includes the standard boilerplate to initialize rclpy, instantiate the node, rclpy.spin() the node, and cleanly shut down.

### Step 3: The Subscriber Node (listener.py)

Create a second Python script that does the following:

* Inherits from the Node class.

* Creates a subscriber to the /random_number topic.

* In the callback function, takes the received float, multiplies it by 2, and uses self.get_logger().info() to print a message like: "Received: [X]. Multiplied value: [Y]".

### Step 4: Update Configuration Files

* Update setup.py in your package to include entry points for both your talker and listener executables so that ros2 run can find them.

* Update package.xml to include your name, email, and a brief description and make sure it contains all the packages that you require.

Step 5: Build and Test

* Navigate back to the root of your workspace (cd ~/qstp_ws).

* Run colcon build.

* Open two separate terminals. Remember to source install/setup.bash in both of them.

* In Terminal 1: ```ros2 run echo_chamber talker```

* In Terminal 2: ```ros2 run echo_chamber listener```

---

## Submission Instructions

Once your nodes are successfully communicating, stage your code, commit your changes, and push them to your `ERC_ROS2_QSTP_26` GitHub repository.

```bash
cd ~/qstp_ws/src
git add echo_chamber/
git commit -m "Week 0 Echo Chamber assignment"
git push -u origin main
```

In the classroom, you need to submit:
* Your Github Repository (make sure its public)
* A screen recording (max 10-15 seconds) showing your final results in the terminal.