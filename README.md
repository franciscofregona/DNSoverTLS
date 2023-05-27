# This file and all the accompanying are part of my submittal for the opening at the S.R.E. team on N26.

Francisco Fregona, franciscofregona@gmail.com
09/03/18

How to run this project
-----------------------

On a console, with docker correctly installed and configured,
Create the DNS proxy server container and launch it with

docker build -t server:v1 -f server/Dockerfile ./server/
docker run -it server:v1

By default, it will start serving on all interfaces, on TCP port 53, and will contact cloudflare on IP 1.1.1.1.

After the first client connected and served it will exit.

How to test this project
------------------------

Assuming the DNS proxy was created and launched correctly in the previous step, and that it took 172.17.0.2 IP address, create and launch the client container with

docker build -t client:v1 -f client/Dockerfile ./client/
docker run -it client:v1

which will contact the server at said IP address and query it for the address for www.yahoo.com.es (using the _dq_ utility), and exit immediately after.

Implementation and choices
--------------------------

I chose to implement the bare minimum of what was asked. Real world chores imposed some time constraints and I wanted to make sure to deliver something. Yet, I managed to integrate some boilerplate code I like to use on my tools, namely, logging and argument support.

The solution works as requested by listening on the TCP port 53. I started working on the solution for it to listen also on the UDP port (which would need to prepend the package received with it's size, packed in 2 bytes), but in order for it to make a clean code I started messing with a loop with threads and time was running out, so I ditched it (for now at least).

In order for me to quickly test and debug the solution, I opted to include a client container, which installs and uses the dq program. Without it, the Ubuntu container would contact the DNS service via the UDP protocol. It was faster to implement this than to find out how to convince Ubuntu to use TCP for it =)

What are the security concerns for this kind of service?
--------------------------------------------------------

While it is somewhat hard to achieve, it is still possible for an attacker to tamper with elements within the docker architecture. Recently published exploits such as Spectre and Meltdown could theoretically violate the jail of both virtualization and containerization, by reading and accessing memory outside the bounds of the process they are run in.

Therefore, it would be nice to increase security measures even inside the relatively safe environment that cloud-computing offers wherever possible.

This little proxy server works just fine as a proof of concept (of my abilities as a coder, at the very least), but in a real world application I'd like it to add authentication of some sort for the containers involved:
Forcing the client-proxy interaction to be DNS over TCP over TLS would render the proxy useless =), but a lighter checking would be nice. I imagine a simple check of version of the software run by the clients and the server would help avoid improper usage from rogue containers by mistake or attack.

I'd also monitor both the checksum of the _server.py_ binary and the state of the service: if this container fails, every other client that depends on it wouldn't be able to reach the internet, it should be restarted immediatly.

Maybe even make it work on a non standar port.

Considering a microservice architecture; how would you see this the dns to dns-over-tls proxy used?
---------------------------------------------------------------------------------------------------

In the context of containers, I find this solution useful as means of reaching the outside world in a little more secure way (avoiding potential eavesdropping and man-in-the-middle attacks) and getting ahold of tools and, mainly, code and resources. For example: a container that contacts github for the latest version of the program it will run.

It will collide, however, with the speed and safety of acquiring said code during build time: the speed at which new containers can be created and deployed minimizes this utility. Depending on the tipical life of the container, it could even make sense to resolve every needed address at build time and stamping the resolved addresses in the containers /etc/hosts file. A somewhat hacky but highly efficient solution.

It will depend, at last, of the design of the pipeline in use. I think it could make a lot of sense on finding static resources, too great in number to set in stone in the /etc/hosts file at build-time and grant security for the user and avoid defacing attacks. e.g.: gotcha images from a 3rd party service.


What other improvements do you think would be interesting to add to the project?
-------------------------------------------------------------------------

The first improvement would be of course allowing multiple incoming requests at the same time and handling UDP requests on the input. I think I can make it with a little more time.

Measure its performance and act upon that: Python is not famous for its performance and it could be an issue. I don't really think so, but it is safer to measure.

A cache for most frequent used domains would be nice, as it would shave some seconds and traffic (not a lot on a single use case, but in a massive deployment, the savings could be something to take into account). Being used exclusively on a relatively known environment (i.e. always the same containers), a high hit-ratio could be reached with minimum resources. I'd write it on a simple dictionary of 'Domain': (response, age_seconds, hits). And every hit on it would decrease the hits counter by 1, and if it gets to zero (or the timestamp shows the age of the record), a new query is forced for the DNS server.

This proxy container should report metrics too, as any service of interest.