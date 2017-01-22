# LK373A Reversing
My discoveries upon purchasing a [Kooye HDMI Extender LKV373A V3.0](https://www.amazon.com/gp/product/B01GZU7ZBA) from Amazon for $40

The unit I received in January 2017 had firmware `4.0.0.0.20160722` and encoder `7.1.2.0.11.20160722`. This version does not have the 'Zero length UDP packet bug' as described by [@OpenTechLabChan](https://twitter.com/OpenTechLabChan) [here](https://opentechlab.org.uk/videos:003:notes) and [Danman](https://blog.danman.eu/new-version-of-lenkeng-hdmi-over-ip-extender-lkv373a/)

## Streaming Video
Using [VLC](http://videolan.org), the stream can be viewed by using `Open Network Stream` with `rtp://239.255.42.42:5004`

## Networking

The device will request an IP address via DHCP but will fallback to using 192.168.1.238 when  DHCP is unavailable.

Through an nmap scan, we can see that TCP ports 80, 7000, 7001, 7003, and 9001 are open. In addition to this, UDP port 5004 is the source port for the RTP stream, 6000 is the multicast advertisement beacon port, and 9002 is the listening port for the discovery service.

|Proto| Port | Description |
|:--:|:----:|-----|
|TCP|80|Web admin|
|TCP|7000|Unknown|
|TCP|7001|Unknown|
|TCP|7003|Unknown|
|TCP|9001|Device Control 'IPTV_CMD'|
|UDP|5004|Video multicast|
|UDP|6000|Advertisement service|
|UDP|9002|Discovery aervice|

### Advertisement Service
Upon receiving an address via DHCP, the unit sends out an advertisement using Multicast UDP on port 6000.

#### Payload
<tspan style="font-family: consolas,monaco,monospace; font-size: 15px;">0000&nbsp;&nbsp;&nbsp;&nbsp;</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: white; background-color:red;">&nbsp;01 00&nbsp;</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: white; background-color:blue">&nbsp;0a 0a 0a bb&nbsp;</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: black; background-color:yellow">&nbsp;58 1b&nbsp;</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: black; background-color:orange">&nbsp;59 1b&nbsp;</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: white; background-color:green">&nbsp;5b 1b&nbsp;</tspan>
    
#### Structure
- <tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: white; background-color:red;">&nbsp;01 00&nbsp;</tspan> Unknown, possibly unit type?
- <tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: white; background-color:blue">&nbsp;0a 0a 0a bb&nbsp;</tspan> The unit's IPv4 address, 10.10.10.187 in    this case.
- <tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: black; background-color:yellow">&nbsp;58 1b&nbsp;</tspan> Port number 7000
- <tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: black; background-color:orange">&nbsp;59 1b&nbsp;</tspan> Port number 7001
- <tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: white; background-color:green">&nbsp;5b 1b&nbsp;</tspan> Port number 7003

### Device Control

By using [Wireshark](http://wireshark.org) and the IPTV Control Center tool 3.0 from [Danman's GDrive](https://drive.google.com/drive/u/0/folders/0B3mWuDyxrXyKZkxwYi1JNllENXc) I was able to observe a discovery protocol broadcast to 255.255.255.255 on UDP port 9002, and a control protocol spoken to TCP port 9001 on the device.

The control protocol is a bit strange in that even though TCP is being used, the device doesn't talk back and forth over a single connection but rather closes the connection after receving the request and then connecting back to the IP and port specified in the request to send its response.

#### Discovery
##### Request
<tspan style="font-family: consolas,monaco,monospace; font-size: 15px;">0000&nbsp;&nbsp;&nbsp;&nbsp;</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: white; background-color:red">&nbsp;49 50 54 56 5f 43 4d 44&nbsp;</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: white; background-color:blue">&nbsp;0a 0a 0a 49&nbsp;</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: black; background-color:yellow">&nbsp;23 2a&nbsp;</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: black; background-color:orange">&nbsp;74 00&nbsp;</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold;">&nbsp;&nbsp;&nbsp;&nbsp;</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: white; background-color:red">&nbsp;IPTV_CMD</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: white; background-color:blue">...I</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: black; background-color:yellow">#*</tspan><tspan style="font-family: consolas,monaco,monospace; font-size: 15px; font-weight: bold; color: black; background-color:orange">&nbsp;t.&nbsp;</tspan>
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a 49 23 2a 74 00  IPTV_CMD...I#*t.
0010   fe 00 0b 09 00 00 00 00 00 00 00 00 00 00 00     ...............```

##### Response
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a bb 23 29 74 00  IPTV_CMD....#)t.
0010   ff 00 2d 2c 54 58 5f 30 30 33 42 34 46 41 35 31  ..-,TX_003B4FA51
0020   37 32 30 00 00 00 00 00 00 00 00 00 00 00 00 00  720.............
0030   00 00 00 00 0a 0a 0a bb 23 29 ff ff 01 01 00 01  ........#)......
0040   c0                                               .```

#### Get Name
##### Request
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a 49 23 29 74 00  IPTV_CMD...I#)t.
0010   1f 00 02 21 00 00                                ...!..```

##### Response
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a bb 23 29 74 00  IPTV_CMD....#)t.
0010   20 00 21 41 54 58 5f 30 30 33 42 34 46 41 35 31   .!ATX_003B4FA51
0020   37 32 30 00 00 00 00 00 00 00 00 00 00 00 00 00  720.............
0030   00 00 00 00 9a                                   .....```
last byte is sum(payload bytes), & 0xff (checksum)

#### Get Video Lock
aka is input video active?
##### Request
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a 49 23 29 74 00  IPTV_CMD...I#)t.
0010   11 00 02 13 00 00                                ......```

##### Response
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a bb 23 29 74 00  IPTV_CMD....#)t.
0010   12 00 03 15 00 01 01                             .......```
0 = no lock, 1 = locked

#### Get IP Config
##### Request
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a 49 23 29 74 00  IPTV_CMD...I#)t.
0010   19 00 02 1b 00 00                                ......```

##### Response
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a bb 23 29 74 00  IPTV_CMD....#)t.
0010   1a 00 0e 28 00 c0 a8 01 01 ff ff ff 00 c0 a8 01  ...(............
0020   fe ce                                            ..```
14 40 0 192.168.1.1 255.255.255.0 192.168.1.254

#### Get FHD Bitrate (1080p)
##### Request
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a 49 23 29 74 01  IPTV_CMD...I#)t.
0010   09 00 02 0c 00 00                                ......```
##### Response
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a bb 23 29 74 01  IPTV_CMD....#)t.
0010   0a 00 04 0f 00 3a 98 d2                          .....:..```
3a98 = 15000
#### Get HD Bitrate (720p)
##### Request
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a 49 23 29 74 01  IPTV_CMD...I#)t.
0010   09 00 02 0c 01 01                                ......```
##### Response
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a bb 23 29 74 01  IPTV_CMD....#)t.
0010   0a 00 04 0f 00 2e e0 0e                          ........```
2e e0 = 12000
#### Get SD Bitrate
##### Request
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a 49 23 29 74 01  IPTV_CMD...I#)t.
0010   09 00 02 0c 02 02                                ......```
##### Response
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a bb 23 29 74 01  IPTV_CMD....#)t.
0010   0a 00 04 0f 00 0f a0 af                          ........```
0xfa0 = 4000
#### Get Baud Rate
##### Request
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a 49 23 29 74 00  IPTV_CMD...I#)t.
0010   17 00 02 19 00 00                                ......```
##### Response
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a bb 23 29 74 00  IPTV_CMD....#)t.
0010   18 00 06 1e 00 00 01 c2 00 c3                    ..........```
01c200 = 115200 baud
#### Get MAC Address
##### Request
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a 49 23 29 74 00  IPTV_CMD...I#)t.
0010   1b 00 02 1d 00 00                                ......```

##### Response
```
0000   49 50 54 56 5f 43 4d 44 0a 0a 0a bb 23 29 74 00  IPTV_CMD....#)t.
0010   1c 00 08 24 00 00 3b 4f a5 17 20 66              ...$..;O.. f```
00:3b:4f:a5:17:20
