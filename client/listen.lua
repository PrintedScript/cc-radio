local radio_proxy_url = "ws://127.0.0.1:8080/ws"

local dfpwm = require("cc.audio.dfpwm")
local speaker = peripheral.find("speaker")

local decoder = dfpwm.make_decoder()
while true do
    local success, message = pcall(function()
        local websocket = http.websocket(radio_proxy_url)
        if websocket ~= false then
            while true do
                local success, message = pcall(function()
                    local starttime = os.time("utc") * 60 * 60
                    local chunk = websocket.receive()
                    local buffer = decoder(chunk)

                    speaker.playAudio(buffer)
                    local endtime = os.time("utc") * 60 * 60
                    local duration = endtime - starttime
                    print("[ "..os.date("%c").." ] [INFO] - Radio chunk played in "..tostring(duration).." seconds")
                end)
                if not success then
                    print("[ "..os.date("%c").." ] [FAIL] - Error Occured: "..message)
                end
            end
        else
            print("[ "..os.date("%c").." ] [FAIL] - Failed to connect to radio proxy, retrying in 5 seconds.")
            os.sleep(5)
        end
    end)
    if not success then
        print("[ "..os.date("%c").." ] [FAIL] - Disconnected from radio proxy, retrying in 5 seconds.")
    end
end