Index = [0,1,2,3,4,5,6,7,8,9];
Data = [10,11,12,13,14,15,16,17,18,19];
server_array = [Index(:) Data(:)];
server_table = array2table(server_array,'VariableNames',{'Index','Data'}); % server table is constructed

server = tcpserver("127.0.0.5",6006,"Timeout",60,"ConnectionChangedFcn",@connectionFcn); % server object is created at localhost and port 6006
while true
    if server.NumBytesAvailable>0

        request = read(server,server.NumBytesAvailable,"string");
        disp(request)
        request_list = split(request, ["=",";"]);
        % COMMAND FORMAT IS -> OP=XXX;IND=Ind1,Ind2;DATA=data1,data2;
        request_op = request_list(2);
        if request_op=="GET"
            indices = split(request_list(4),","); % get the indices
            data = [];
            for i=indices
                data = [data, server_table.Data(str2double(i)+1)];
            end
            resp_string = "DATA=";
            for i=1:length(data)
                resp_string = resp_string + num2str(data(i));
                resp_string = resp_string + ",";
            end
            resp_string = (resp_string{1}(1:end-1))+";"; % drop last comma and put semi colon 
            while true
                if(server.Connected==1)
                disp("connection stable")
                write(server,resp_string,"string");
                break
                end
            end
           
            disp(server_table);
        
        elseif(request_op=="PUT")
            indices = split(request_list(4),","); % get the indices
            data_values = split(request_list(6),",");
            for i=1:length(indices)
                server_table.Data(str2double(indices(i))) = str2double(data_values(i));
            end
            disp(server_table)
        
        elseif(request_op=="CLR")
            %clear the Data
            server_table.Data = [0;0;0;0;0;0;0;0;0;0];
            %no need to response
            disp(server_table);
        end
    
    end

end

function connectionFcn(src,~)
    if src.Connected
       disp("Client Connected")
    else
       disp("Client has disconnected.")
    end
end
