in this application you can run a server and a client with -s or -c  

to run the server use the following flags:   
-s to specify that its the server you want to run  
-i type in the server ip adress  
-p specify the port number you will be using  
-r choose from 3 different  reliablity methods, you can choose from 'stop_and_wait' , 'GBN' or 'SR'
-t choose from 2 different test cases, 'skip_ack' or 'loss'  

The server/receiver can be invoked with:  
python3 application.py -s -i <ip_address> -p <port_number> -r <reliable_method>  
With test cases:  
python3 application.py -s -i <ip_address> -p <port_number> -r <reliable_method> -t <test_case>  


to run the client  
-c to envoke the client side.  
-i type in the server ip adress  
-p type in the port number that the server is using  
-r specify the SAME reliability method as the server is running in  
-f specify the filename you will be transferring, there is a picture of a dog in the applications ready to be transferred.  
-t specify the SAME test case as the server is running in  

The client/sender can be invoked with:    
python3 application.py -c -i <ip_address> -p <port_number> -r <reliable_method>  
With test cases:  
python3 application.py -c -i <ip_address> -p <port_number> -r <reliable_method> -t <test_case> 


