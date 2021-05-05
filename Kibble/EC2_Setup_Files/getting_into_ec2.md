# Getting into EC2 [1]:

**Sign in to AWS:**</br>
https://aws.amazon.com/ </br>
contact@beagleai.com</br>
Beagleai20!

**Go to the EC2 Console/Dashboard:**</br>
All services – compute – EC2 

**Launch Instance:**

1.	Select an OS</br>
Ubuntu 18
2.	Choose a tier (instance type)</br>
Choose t2.micro (“free tier eligible”) unless you need something specific (e.g. Torch only installs on a *.medium or larger instance due to memory requirements)
3.	Configure</br>
Leave defaults
4.	Storage</br>
The default 8GB should be fine unless you know you need more
5.	Add tags  (just ignore this)</br>
6.	Set the security group</br>
See below (at launch).
7.	Launch and set the keypair</br>
See below (at launch).

View instances with:  EC2 Dashboard – Left nav pane – Instances - Instances

**Security Groups:**

Security groups define rules that set the inbound and outbound traffic from the instance.  To be able to access it, you need to set a rule that will allow your IP inbound. This can be done when the instance is launched (step 6 above).

_At launch:_ when launching a new instance, you must assign a security group.  This can be done by assigning an existing group or creating a new group.  If you create a new group, you can set the rules (these are inbound rules).  Set a rule with type “all traffic” or “ssh” and set source to “My IP”. Without a rule that allows your IP, it won’t let you in. [2][3]

_After launch:_ EC2 Dashboard – left nav pane – Network & Security – Security Groups.  OR probably more usefully, go to the instances list, select the instance id you want, security tab – click on security group ID.

**Keypairs:**

_At Launch:_  Use an existing key if you have one. If you don’t, make a new one, download it, and put it somewhere on your machine like “~/.ssh/”.  Make it private with `chmod 400 <keyname.pem>`

You can view the keypairs and perform operations with them by navigating in the EC2 dashboard – left nav pane – Network & Security – Key Pairs

Additional keys can be added after initial setup.  The process is explained in the AWS documentation [4].  A new key pair is made, the public key extracted, and then the key is placed on the server.

**Accessing the EC2 Instance:**

In the instances view, select the instance and click connect at the top of the page.  “ssh client” has the commands you need.

`ssh -i "<keyname.pem>" ubuntu@<public dns>`

`sftp -o "IdentityFile=<keyname.pem>" ubuntu@<public dns>`

`scp -i "<keyname.pem>" local\_file ubuntu@<public dns>`

`<keyname.pem>` is the path of the key file you created when creating the instance
The public dns of the server is "ubuntu@ec2-\<ip\>.\<region\>.compute.amazonaws.com"


**Cost Information:**

The Billing Dashboard is available in a dropdown menu by clicking the username in the top right of the page.

To see spending: Go to Cost Explorer on the left, and then select daily reports.

Free tier is limited to 750 hrs/month

<span style="color:red">Which instances are hourly and which are by the second?</span>


**Links:**

[1] [https://docs.aws.amazon.com/ec2/index.html]() </br>
[2] [https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-set-up.html]() </br>
[3] [https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/authorizing-access-to-an-instance.html#add-rule-authorize-access]() </br>
[4] [https://aws.amazon.com/premiumsupport/knowledge-center/new-user-accounts-linux-instance/]()

