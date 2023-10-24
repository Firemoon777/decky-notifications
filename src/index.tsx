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
  findInReactTree,
  afterPatch,
  wrapReactType,
  Patch,
  sleep
} from "decky-frontend-lib";

import { ReactElement, VFC, createElement } from "react";
import QRCode from "react-qr-code";

import { FaBullhorn } from "react-icons/fa";


const Content: VFC<{ serverAPI: ServerAPI }> = ({serverAPI}) => {
  const getServerAddress = async () => {
    const result = await serverAPI.callPluginMethod<any, string>("get_ip_address", {});
    return result.result
  }

  return (
    <PanelSection title="Panel Section">
      <PanelSectionRow>
        <ToggleField label="Enabled" checked/>
        <ToggleField label="Play sound" checked/>
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={async (e) => {
              let data = {
                address: await getServerAddress(),
                port: 7894,
                password: "secure"
              }
              showContextMenu(
                <Menu label="Connection" cancelText="OK" onCancel={() => {}}>
                  <MenuItem><div style={{background: 'white', padding: '16px', width: "100%"}}><QRCode value={JSON.stringify(data)}/></div></MenuItem>
                  <MenuItem>Scan QR Code with<br/>Decky Notification Transmitter</MenuItem>
                  <MenuItem>Address: {data.address}</MenuItem>
                  <MenuItem>Port: {data.port}</MenuItem>
                  <MenuItem>Password: {data.password}</MenuItem>
                </Menu>,
                e.currentTarget ?? window
              )
            }
          }
        >
          Show Connection QR Code
        </ButtonItem>
      </PanelSectionRow>
    </PanelSection>
  );
};

function createNotification(toast_data: any) {
  window.DeckyPluginLoader.toaster.toast({
    //title: "Test",
    body: <a onClick={async (e: any) => {
      Router.Navigate("/decky-plugin-test")
    }}>Reply</a>
  })
}

const DeckyPluginRouterTest: VFC = () => {
  return (
    <div style={{ marginTop: "50px", color: "white" }}>
      Hello World!
      <DialogButton onClick={() => Router.NavigateToLibraryTab()}>
        Go to Library
      </DialogButton>
    </div>
  );
};

class Message {
  array: Array<string>;
  arrayIndexOffset_: number = -1;
  convertedPrimitiveFields = {};
  messageId_ = undefined;
  pivot_: number = 1.7976931348623157e+308;
  wrappers = null

  constructor() {
    this.array = new Array(
      "some-id",
      "some-steam-id",
      "title",
      "body",
      "icon"
    )
  }

  tag = () => this.array[0]
  set_tag = (x: string) => { this.array[0] = x }

  steamid = () => this.array[1]
  set_steamid = (x: string) => {this.array[1] = x }

  title = () => this.array[2]
  set_title = (x: string) => {this.array[2] = x }

  body = () => this.array[3]
  set_body = (x: string) => {this.array[3] = x }

  icon = () => this.array[4]
  set_icon = (x: string) => {this.array[4] = x }

  notificationid() {
    return null;
  }

  response_steamurl() {
    return null
  }  

  serializeBinary() {
    console.error("serializeBinary =(")
  }

  serializeBase64String() {
    console.error("serializeBase64String =(")
  }

  // NotificationStore.m_cbkNotificationTray.Dispatch(NotificationStore.m_rgNotificationTray)
}

class DeckyPluginNotificationsSharedMethods {
  serverAPI: ServerAPI;

  constructor(serverAPI: ServerAPI) {
    this.serverAPI = serverAPI;
  }

  SendPairNotificationRequest(device: any) {
    let self = this
    DeckyPluginLoader.toaster.toast({
      title: "Pairing " + device.name + ", key: " + device.key,
      duration: 15_000,
      body: <a href="#" onClick={async (e: OnClickEvent<HTMLInputElement>) => {
        console.log(e)
        await self.serverAPI.callPluginMethod("trust_device", {device_id: device.id})
        e.srcElement.innerHTML = "Accepted";
        e.srcElement.onClick = null;
      }}>Click to accept</a>
    })
  }

  SendNotification(data: any) {
    let logo = null;
    if(data.icon) {
      logo = <img style={{height: "100%"}} src={data.icon}/>;
    }
    DeckyPluginLoader.toaster.toast({
      title: data.title,
      body: data.body,
      logo: logo
    })
  }

  createPayload() {
    return {
      eType: 8,
      notifications: Array(
        {
          bNewIndicator: true,
          data: new Message(),
          eSource: 1,
          eType: 8,
          nToastDurationMS: 5000,
          notificationID: 9001,
          rtCreated: Date.now(),
          rtMenuFirstViewed: null,
        }
      )
    }
  }
}

export default definePlugin((serverApi: ServerAPI) => {
  serverApi.routerHook.addRoute("/decky-plugin-test", DeckyPluginRouterTest, {
    exact: true,
  });

  window.DeckyPluginNotificationsSharedMethods = new DeckyPluginNotificationsSharedMethods(serverApi);

  /*let notification_tab = findInReactTree(notification_div, (x: ReactElement) => {
    return x?.memoizedProps?.NavigationManager
  })
  window.notificaion_tab = notification_tab;

  let notification_entry = findInReactTree(notification_tab, (x: ReactElement) => {
    return x?.memoizedProps?.className?.includes("standardtemplates_StandardTemplateContainer_1adpx")
  })
  window.notification_entry = notification_entry;*/

  let notification_div_f = (x: ReactElement) => {
    return x?.memoizedProps?.className?.includes(["quickaccesscontrols_QuickAccessNotifications"])
  }

  let patch: Patch | null = null;
  (async () => {
    let notification_div = findInReactTree(DeckyPluginLoader.tabsHook.qAMRoot, notification_div_f)
    while(!notification_div) {
      notification_div = findInReactTree(DeckyPluginLoader.tabsHook.qAMRoot, notification_div_f)
      await sleep(5000)
    }
    console.log("Notification tab found")
    window.notification_div = notification_div;

    let notification_tab = findInReactTree(DeckyPluginLoader.tabsHook.qAMRoot, (x: ReactElement) => {
      return x?.memoizedProps?.className?.includes("tab_Notifications")
    })
    window.notification_tab = notification_tab;
  
    //wrapReactType(notification_div)
    /*patch = afterPatch(notification_tab.type, 'render', (_: any[], ret: ReactElement) => {
      console.warn("ok!")
      console.log(ret)
      return ret
    })*/
    wrapReactType(notification_div.return.type)
    patch = afterPatch(notification_div.return, 'type', (_: any[], ret: ReactElement) => {
      console.warn("ok!")
      console.log(ret)
      return ret
    })
  })();
  
  
  return {
    title: <div className={staticClasses.Title}>Example Plugin</div>,
    content: <Content serverAPI={serverApi} />,
    onDismount() {
      serverApi.routerHook.removeRoute("/decky-plugin-test");
      //patch?.unpatch();
    },
    icon: <FaBullhorn/>
  };
});
