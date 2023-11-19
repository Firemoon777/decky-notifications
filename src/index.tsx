import {
  ButtonItem,
  definePlugin,
  DialogButton,
  Menu,
  MenuItem,
  PanelSection,
  PanelSectionRow,
  Router,
  ServerAPI,
  showContextMenu,
  staticClasses,
  ToggleField,
} from "decky-frontend-lib";

import { VFC, useEffect, useState } from "react";

import { FaMobile, FaDesktop, FaLaptop, FaTablet, FaTv, FaQuestion, FaPlug } from "react-icons/fa";

const Content: VFC<{ serverAPI: ServerAPI }> = ({serverAPI}) => {
  const getDeviceList = async () => {
    const result = await serverAPI.callPluginMethod<any, string>("device_list", {});
    return result.result
  }

  const getNotificaionList = async () => {
    const result = await serverAPI.callPluginMethod<any, string>("notification_list", {});
    return result.result
  }

  const [notifications, setNotifications] = useState([]);
  const [devices, setDevices] = useState([]);


  useEffect(() => {
    let f = async () => {
      let d = await getDeviceList()
      setDevices(d);

      let n = await getNotificaionList()
      setNotifications(n);
    };
    const id = setInterval(f, 1000);
  
    f();
    return () => clearInterval(id);  
  }, []);

  let getNotifications = () => {
    let content = []
  
    for(let n of notifications) {
      let img = "";
      if(n.icon) {
        img = <img src={n.icon} align="left" alt="Notification icon" style={{height: "100%"}}/>
      }
      content.push(
        <PanelSection title={"[" + n.appName + "] " + n.title}>
          <PanelSectionRow>{n.body}</PanelSectionRow>
        </PanelSection>
      )
    }

    if (notifications.length > 0) {
      content.push(
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={async (e) => {
              await serverAPI.callPluginMethod<any, string>("notifications_clear", {})
            }}
          >Clear</ButtonItem>
        </PanelSectionRow>
      )
    }

    return content;
  } 

  const getDevices = (f: Function) => {
    let content = [];
    for(let dev of devices) {
        if(!f(dev)) {
          continue;
        }
        let icon;
        switch(dev.type) {
          case 'desktop': 
            icon = <FaDesktop/>
            break
          case 'laptop': 
            icon = <FaLaptop/>
            break
          case 'phone':
            icon = <FaMobile/>
            break
          case 'tablet': 
            icon = <FaTablet/>
            break
          case 'tv':
            icon = <FaTv/>
            break
          default:
            icon = <FaQuestion/>
            break
        }

        let untrust = async () => {
          await serverAPI.callPluginMethod("trust_device", {device_id: dev.deviceId, trust: false})
        }
        /*
                      <MenuItem onSelected={() => {}}>Local fingerprint: {(await serverAPI.callPluginMethod<any, string>("local_fingerprint", {})).result}</MenuItem>
                      <MenuItem onSelected={() => {this.cancel()}}>Remote fingerprint:<br/>{dev.fingerprint}</MenuItem>
        */
        content.push(
          <PanelSectionRow>
            <ButtonItem
              layout="below"
              onClick={async (e) => {
                  showContextMenu(
                    <Menu label={dev.name} cancelText="Close" onCancel={() => {}}>
                      <MenuItem onSelected={untrust}>Remove device</MenuItem>
                    </Menu>,
                    e.currentTarget ?? window
                  )
                }
              }
            >
              {icon} {dev.name}
            </ButtonItem>
          </PanelSectionRow>
        )
        
    }
    return content;
  }

  /*
      <PanelSection title="Settings">
        <PanelSectionRow>
          <ToggleField label="Play sound" checked="false"/>
        </PanelSectionRow>
      </PanelSection> 
  */

  return (
    <div>
      <PanelSection title="Trusted Devices">
        {getDevices((dev) => dev.is_trusted === 1)}
      </PanelSection>
      <PanelSection title="Recent Notifications">
        {getNotifications()}
      </PanelSection>
    </div>
  );
};

export default definePlugin((serverApi: ServerAPI) => {  
  const getEvent = async () => {
    return await serverApi.callPluginMethod<any, any>("get_event", {});
  }

  let interval = setInterval(async () => {
    let data = await getEvent();
    if(!data.result) return;

    let event = data.result;

    console.log(event)

    if(event.event === "pair") {
      DeckyPluginLoader.toaster.toast({
        title: "Pairing " + event.deviceName + ", key: " + event.verificationKey,
        duration: 15_000,
        body: <a href="#" onClick={async (e) => {
          e.persist()
          await serverApi.callPluginMethod("trust_device", {device_id: event.deviceId})
          e.target.outerHTML = "Accepted";
          e.target.onClick = null;
        }}>Click to accept</a>
      })
      return;
    }

    if(event.event === "notification") {
      let logo = null;
      if(event.icon) {
        logo = <img style={{height: "100%"}} src={event.icon}/>;
      }
      DeckyPluginLoader.toaster.toast({
        title: event.title,
        body: event.body,
        logo: logo
      })
      return;
    }
  }, 1000)

  return {
    title: <div className={staticClasses.Title}>Decky Notifications</div>,
    content: <Content serverAPI={serverApi} />,
    onDismount() {
      clearInterval(interval);
    },
    icon: <FaPlug/>
  };
});
