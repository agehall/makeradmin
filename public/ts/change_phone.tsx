import * as common from "./common"
import * as login from "./login"
import { UNAUTHORIZED } from "./common";
import {Component, render} from "preact";

declare var UIkit: any;

interface State {
    requestSubmitInProgress: boolean,
    requestSent: boolean,
    validateSubmitInProgress: boolean,
    phoneSent: string,
    requestCount: number,
}

interface Props {
    id: number
}

class ChangePhone extends Component<Props, State> {
    
    constructor(props: any) {
        super(props);
        this.state = {
            requestSubmitInProgress: false,
            requestSent: false,
            validateSubmitInProgress: false,
            phoneSent: "",
            requestCount: 0
        }
    }

    async submitPhoneNumber(number: string) {
        try {
            this.setState({requestSubmitInProgress: true})
            const {data} = await common.ajax("POST", `${window.apiBasePath}/member/current/change_phone_request`, {phone: number.trim()});
            this.setState({requestSent: true, phoneSent: data.phone, requestCount: data.request_count});
        } catch (error: any) {
            if (error.status === UNAUTHORIZED) {
                login.redirect_to_member_page();
            } else {
                common.show_error("Byta telefonnummer misslyckades", error)
            }
        }
        this.setState({requestSubmitInProgress: false})
    }
    
    async submitValidationCode(code: string) {
        try {
            this.setState({validateSubmitInProgress: true})
            let number = Number.parseInt(code.trim());
            if (isNaN(number)) {
                throw new Error("Koden måste vara en siffra.")
            }
            await common.ajax("POST", `${window.apiBasePath}/member/current/change_phone_validate`, {validation_code: number});
            window.location.href = "/member";
        } catch (error: any) {
            if (error.status === UNAUTHORIZED) {
                login.redirect_to_member_page();
            } else {
                common.show_error("Validera kod misslyckades", error)
            }
        }
        this.setState({validateSubmitInProgress: false})
    }
    
    render() {
        const {requestSubmitInProgress, validateSubmitInProgress, requestSent, phoneSent, requestCount} = this.state;
        
        return <>
            <form className="uk-form uk-form-stacked uk-margin-bottom"
                  onSubmit={e => {
                      e.preventDefault();
                      const input = document.getElementById('phone') as HTMLInputElement;
                      if (input != null) {
                          this.submitPhoneNumber(input.value);
                      }
                  }}
            >
                <h1 style="text-align: center;">Nytt telefonnummer</h1>
                <div className="uk-form-row" style="margin: 16px 0;">
                    <input id="phone" tabIndex={1} autoFocus className="uk-form-large uk-width-1-1" type="tel"  placeholder="Telefonnummer"/>
                </div>
                <div className="uk-form-row" style="margin: 16px 0;">
                    <button className="uk-width-1-1 uk-button uk-button-primary uk-button-large" disabled={requestSubmitInProgress}><span className="uk-icon-check"/>Skicka valideringskod</button>
                </div>
            </form>
            <p style={{visibility: requestSent ? "visible" : "hidden", color: "green", fontWeight: "bold"}}>SMS{requestCount>1?` #${requestCount}`:""} med valideringskod skickad till {phoneSent}, skriv in koden (eller tryck "skicka" igen för en ny kod).</p>
            <form className="uk-form uk-form-stacked uk-margin-bottom"
                  onSubmit={e => {
                      e.preventDefault();
                      const input = document.getElementById('code') as HTMLInputElement;
                      if (input != null) {
                          this.submitValidationCode(input.value);
                      }
                  }}
            >
                <h1 style="text-align: center;">Validera telefonnummer med kod</h1>
                <div className="uk-form-row" style="margin: 16px 0;">
                    <input id="code" tabIndex={2} autoFocus className="uk-form-large uk-width-1-1"
                           type="number" placeholder="Valideringkod"/>
                </div>
                
                <div className="uk-form-row" style="margin: 16px 0;">
                    <button className="uk-width-1-1 uk-button uk-button-primary uk-button-large"
                            disabled={validateSubmitInProgress}><span className="uk-icon-check"/>Validera
                    </button>
                </div>
            </form>
        </>;
    }
}


common.documentLoaded().then(() => {
    common.addSidebarListeners();
    
    const content = document.getElementById("content")
    if (content != null) {
        render(<ChangePhone id={1}/>, content);
    }
});
