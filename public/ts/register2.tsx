import * as common from "./common";
import { Component, ComponentChildren, createContext, render } from 'preact';
import { StateUpdater, useContext, useEffect, useMemo, useRef, useState } from 'preact/hooks';
import { ServerResponse } from "./common";
import { Translation, TranslationKeyValues } from "./translate";
import { PaymentAction, PaymentIntentNextActionType, Purchase, display_stripe_error, stripe } from "./payment_common";
import { PopupModal, PopupWidget, useCalendlyEventListener } from "react-calendly";
import { FACEBOOK_GROUP, GET_STARTED_QUIZ, INSTAGRAM, RELATIVE_MEMBER_PORTAL, SLACK_HELP, WIKI } from "./urls";
import { LoadCurrentMemberInfo, member_t } from "./member_common";

declare var UIkit: any;

type Dictionary = Translation<typeof Eng>;
type TranslationKey = TranslationKeyValues<typeof Eng>;

type Plan = {
    id: PlanId,
    title: string,
    abovePrice: string,
    price: number,
    period: string,
    description: string,
    products: Product[],
    subscriptions: SubscriptionType[]
    highlight: string | null,
}

const Eng = {
    continue: "Continue",
    back: "Back",
    apply_for_discounts: "I cannot afford the membership fee",
    summaries: {
        labaccess_subscription: {
            summary: "Makerspace Access - 1 month",
            renewal: (price: number) => `Your makerspace access will renew monthly at ${price} kr/month.`,
        },
        membership_subscription: {
            summary: "Base Membership - 1 year",
            renewal: (price: number) => `Your base membership will renew yearly at ${price} kr/year.`,
        },
        labaccess: {
            summary: "Makerspace Access - 1 month",
        },
        starter_pack: {
            summary: "Starter Pack - 2 months",
        },
        renewal: {
            one: "You can cancel this subscription at any time.",
            many: "You can cancel these subscription at any time."
        },
        cart_total: "Total",
        payment_right_now: "Right now, you will pay",
    },
    memberships: {
        title: "Makerspace Memberships",
        p1: "Memberships are split into two parts",
        p2: "Everyone has the base membership, and if you want to work on your own projects, you must also get Makerspace Access.",
    },
    chooseYourPlan: {
        title: "Choose your Makerspace\xa0Access",
        help: ""
    },
    priceUnit: "kr",
    plans: {
        makerspaceAccessSub: {
            title: "Makerspace Access Subscription",
            abovePrice: "base membership +",
            period: "per month",
            description: "A monthly subscription gets you access all the time, for a lower price.\n2 months minimum.",
        },
        starterPack: {
            title: "Starter Pack",
            abovePrice: "base membership +",
            period: "",
            description: "Two months of makerspace access for a lower price.\nNew members only.",
        },
        singleMonth: {
            title: "1 month of Makerspace Access",
            abovePrice: "base membership +",
            period: "",
            description: "One month of makerspace access.",
        },
        decideLater: {
            title: "Base Membership Only",
            abovePrice: "base membership +",
            price: "0",
            period: "",
            description: (a: number, b: number) => `Later, you can pay for individual months of makerspace access (${a} kr/mo) in our webshop, or get a subscription (${b} kr/mo).`,
        },
    },
    baseMembership: {
        title: "Base Membership",
        reasons: [
            "Take part in courses",
            "Attent social events",
            "Vote at yearly meetings",
            "Support your local makerspace"
        ],
        price: "200",
        period: "per year",
    },
    makerspaceAccess: {
        title: "Makerspace Access",
        price: " kr per month",
        requirement: "Requires the base membership",
        reasons: [
            "Access to Stockholm Makerspace 24/7",
            "Work on your own projects",
            "Store a personal box at the space"
        ],
    },
    memberInfo: {
        title: "A little bit about you",
        firstName: "First name",
        lastName: "Last name",
        email: "Email",
        phone: "Phone",
        zipCode: "Zip code",
        submit: "Continue",
    },
    terms: {
        title: "Rules for the premises",
        accept: "Accept",
        pledge: "You must pledge to ...",
        rules: [
            "take responsibility for your own actions and to show consideration for other members.",
            "not do anything illegal on the premises.",
            "abstain from using drugs or alcohol on the premises.",
            "not operate machines while under the influence.",
            "keep yourself updated on the latest rules.",
            "find and follow space- and machine-specific rules.",
            "always clean up after yourself and leave the premises in a clean state.",
            "ask a member of the Board if you're unsure about something.",
            "always ask before taking pictures of people or other people's projects located on the premises.",
            "not engage in commercial activities on the premises.",
            "not sleep on the premises.",
            "retrieve your storage box within 45 days from expiration of your makerspace access. After this period of time, any remaining materials belong to the Stockholm Makerspace.",
            "take full responsibility for what your guests do on the premises. (Your guest is only allowed on the premises if your intention is to show them the space and activities. They must not work on a project of their during their visit.)",
            "always leave the kitchen/common areas in better shape than you found them. This is especially important in areas shared with other building occupants and we risk losing access to these areas if this privilege is abused.",
            "report lost keys to the Board immediately after loss.",
            "report damage to the machines/premises to the Board immediately upon discovery.",
            "not remove equipment from the premises. Stockholm Makerspace does not allow equipment rental or borrowing.",
            "only visit the space when you hold an active membership. If your makerspace access is inactive, you have no access to the premises except as participant in Makerspace run activities such as courses, cleanup days or open days.",
        ],
        understanding1: "I understand that if I violate any of the rules above or otherwise abuse my access to the premises, I may be banned from the premises without a refund of my access fee.",
        understanding2: "I understand that I am solely responsible for everything I do on the premises.",
        welcoming: "I will do my best to ensure that the Stockholm Makerspace is a clean, safe and welcoming place.",
    },
    calendar: {
        title: "Calendar",
        text: (<>Book a Member Introduction, during which you'll get a tour of the space (if you haven't already) and gain permission to use the makerspace.
            Your makerspace access will not be activated until you have visited a Member Introduction.
            In some situations, there may be no available time slots. Please let us know on <a href={FACEBOOK_GROUP}>Facebook</a> or <a href={SLACK_HELP}>Slack</a> if you cannot book a slot.
        </>),
        book_button: "Book a member introduction"
    },
    payment: {
        title: "Payment",
        text: "Almost done, we just need to take care of the payment.",
        pay: "Pay with Stripe",
        payment_processor: "Payment handled by Stripe",
    },
    success: {
        title: "Welcome to the Stockholm\u{00A0}Makerspace!",
        text: <><p>We look forward to meeting you!</p>
            <p>To gain access to the Makerspace you must attend a member introduction. You can book it here, or do it later.</p>
            <p>Here are your next steps:</p>
        </>,
        book_button: "Book your member introduction",
        book_step: "",
        steps: [
            // ((onClick: (e: MouseEvent)=>void) => (<>Book a Member Introduction, during which you'll get a tour of the space (if you haven't already) and gain permission to use the makerspace. Your makerspace access will not be activated until you have visited a Member Introduction.
            // You can find them in the calendar: https://calendly.com/medlemsintroduktion/medlemsintroduktion ("Medlemsintroduktion" in Swedish)</>)),
            ((onClick: (e: MouseEvent) => void) => (<>Join our <a target="_blank" href={SLACK_HELP} onClick={onClick}>Slack</a> to chat with other members.</>)),
            ((onClick: (e: MouseEvent) => void) => (<>Take our <a target="_blank" href={GET_STARTED_QUIZ} onClick={onClick}>Get Started Quiz</a> to learn about the space.</>)),
            ((onClick: (e: MouseEvent) => void) => (<>Check out our <a target="_blank" href={WIKI} onClick={onClick}>wiki</a>.</>)),
            ((onClick: (e: MouseEvent) => void) => (<>Be inspired on <a target="_blank" href={INSTAGRAM} onClick={onClick}>our Instagram</a>.</>)),
        ],
        continue_to_member_portal: "Continue to your member page",
    },
    discounts: {
        title: "Low Income Discounts",
        text: "If you cannot afford the full price of membership, you can apply for a discount.",
        confirmation: <>
            <p>A new option will show up in the plan selection page which gives you a 30% discount.</p>
            <p>We understand that not everyone can afford the full price of membership. But there are other ways you can help, even if you cannot pay.
            The Makerspace is run by its members volonteering their time and effort. Join a work day, help out with maintaining a machine, or why not hold a course about something you are excited about?</p>
            </>,
        submit: "Continue",
        cancel: "Cancel",
        messagePlaceholder: "Tell us why you need a discount, in at least a few sentences.",
        reasons: {
            "student": "I am a student",
            "unemployed": "I am unemployed",
            "senior": "I am a senior citizen",
            "other": "Other",
        }
    }
}

const Swe: typeof Eng = {
    // TODO
    ...Eng,
    continue: "Fortsätt",
}

const Translations: { "en": typeof Eng, "sv": typeof Eng } = {
    "en": Eng,
    "sv": Swe,
}

const TranslationContext = createContext(new Translation(Translations.en));

const useTranslation = (): InstanceType<typeof Translation<typeof Eng>>["t"] => {
    const t = useContext(TranslationContext);
    return t.t.bind(t);
}

const LanguageChooser = ({ setLanguage }: { setLanguage: (lang: keyof typeof Translations) => void }) => {
    return (
        <div className="language-chooser">
            <div className="language-chooser-buttons">
                <button className="language-chooser-button" onClick={() => setLanguage("en")}>English</button>
                <button className="language-chooser-button" onClick={() => setLanguage("sv")}>Svenska</button>
            </div>
        </div>
    );
}

const LabeledInput = ({ label, id, required, type, value, pattern, onChange, onInvalid }: { id: string, type: string, pattern?: string, label: string, required: boolean, value: string, onChange: (value: string) => void, onInvalid: () => void }) => {
    return (
        <div>
            <label for={id} class="uk-form-label">{label}</label>
            <input id={id} class="uk-input" type={type} pattern={pattern} placeholder="" value={value} required={required} maxLength={255} onChange={e => onChange(e.currentTarget.value)} onInvalid={onInvalid} />
        </div>
    )
}

const PlanButton = ({ plan, selected, onClick }: { plan: Plan, selected: boolean, onClick: () => void }) => {
    const t = useTranslation();
    return (
        <div className={"access-plan " + (selected ? 'selected' : '')} onClick={onClick}>
            <div className="access-plan-title">{plan.title}{plan.highlight !== null ? <span class="plan-highlight"><span>{plan.highlight}</span></span> : null}</div>
            <div className="access-plan-price">
                <span class="abovePrice">{plan.abovePrice}</span>
                <span class="price">{plan.price} {t("priceUnit")}</span>
                <span class="period">{plan.period}</span>
            </div>
            <div className="access-plan-description">{plan.description}</div>
        </div>
    );
}

type MemberInfo = {
    firstName: string,
    lastName: string,
    email: string,
    phone: string,
    zipCode: string,
}

type DiscountReason = "student" | "unemployed" | "senior" | "other";

type DiscountsInfo = {
    discountReason: DiscountReason | null,
    discountReasonMessage: string,
}

const BackButton = ({ onClick }: { onClick: () => void }) => {
    const t = useTranslation();
    return (
        <a className="flow-button-back" onClick={onClick}>{t("back")}</a>
    );
}

const MemberInfoForm = ({ info, onChange, onSubmit, onBack }: { info: MemberInfo, onChange: StateUpdater<MemberInfo>, onSubmit: (info: MemberInfo) => void, onBack: () => void }) => {
    const t = useTranslation();
    const [showErrors, setShowErrors] = useState(false);
    const onInvalid = () => setShowErrors(true);
    return (
        <form className={"member-info " + (showErrors ? "validate" : "")} onSubmit={e => {
            e.preventDefault();
            setShowErrors(false);
            onSubmit(info);
        }} onInvalid={() => {
            console.log("invalid");
            setShowErrors(true);
        }}>
            <LabeledInput label={t("memberInfo.firstName")} id="firstName" type="text" required value={info.firstName} onChange={firstName => onChange(info => ({ ...info, firstName }))} onInvalid={onInvalid} />
            <LabeledInput label={t("memberInfo.lastName")} id="lastName" type="text" required value={info.lastName} onChange={lastName => onChange(info => ({ ...info, lastName }))} onInvalid={onInvalid} />
            <LabeledInput label={t("memberInfo.email")} id="email" type="email" required value={info.email} onChange={email => onChange(info => ({ ...info, email }))} onInvalid={onInvalid} />
            <LabeledInput label={t("memberInfo.phone")} id="phone" type="tel" pattern="[\-\+\s0-9]*" required value={info.phone} onChange={phone => onChange(info => ({ ...info, phone }))} onInvalid={onInvalid} />
            <LabeledInput label={t("memberInfo.zipCode")} id="zipCode" type="text" pattern="[0-9\s]*" required value={info.zipCode} onChange={zipCode => onChange(info => ({ ...info, zipCode }))} onInvalid={onInvalid} />
            <input type="submit" className="flow-button" value={t("memberInfo.submit")} />
            <BackButton onClick={onBack} />
        </form>
    )
}

const RuleCheckbox = ({ rule, value, onChange }: { value: boolean, rule: string, onChange: StateUpdater<boolean> }) => {
    const id = `${(Math.random() * 10000) | 0}`;
    return (
        <div class="rule-checkbox">
            <input id={id} type="checkbox" checked={value} onChange={e => onChange(e.currentTarget.checked)} />
            <label for={id}>{rule}</label>
        </div>
    );
}

type Terms = {
    accepted1: boolean;
    accepted2: boolean;
    accepted3: boolean;
}

const TermsAndConditions = ({ onAccept, onBack, acceptedTerms, onChangeAcceptedTerms }: { onAccept: () => void, onBack: () => void, acceptedTerms: Terms, onChangeAcceptedTerms: (terms: Terms)=>void }) => {
    const t = useTranslation();
    return (<div class="terms-and-conditions">
        <h2>{t("terms.title")}</h2>
        <p>{t("terms.pledge")}</p>
        <ol className="rules-list">
            {t("terms.rules").map(rule => <li>{rule}</li>)}
        </ol>

        <RuleCheckbox rule={t("terms.understanding1")} onChange={() => onChangeAcceptedTerms({ ...acceptedTerms, accepted1: !acceptedTerms.accepted1})} value={acceptedTerms.accepted1} />
        <RuleCheckbox rule={t("terms.understanding2")} onChange={() => onChangeAcceptedTerms({ ...acceptedTerms, accepted2: !acceptedTerms.accepted2})} value={acceptedTerms.accepted2} />
        <RuleCheckbox rule={t("terms.welcoming")} onChange={() => onChangeAcceptedTerms({ ...acceptedTerms, accepted3: !acceptedTerms.accepted3})} value={acceptedTerms.accepted3} />
        <button className="flow-button" disabled={!acceptedTerms.accepted1 || !acceptedTerms.accepted2 || !acceptedTerms.accepted3} onClick={onAccept}>{t("terms.accept")}</button>
        <BackButton onClick={onBack} />
    </div>);
}

enum State {
    ChooseLanguage,
    ChoosePlan,
    MemberInfo,
    Terms,
    Calendar,
    Confirmation,
    Success,
    Discounts,
}

const Panel = ({ children }: { children: any }) => {
    return (
        <div className="panel">
            {children}
        </div>
    );
}

const createStripeCardInput = () => {
    // Create an instance of Elements.
    const elements = stripe.elements({ locale: "sv" });
    // Custom styling can be passed to options when creating an Element.
    const stripeStyle = {
        base: {
            color: '#32325d',
            lineHeight: '18px',
            fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
            fontSmoothing: 'antialiased',
            fontSize: '16px',
            '::placeholder': {
                color: '#aab7c4'
            }
        },
        invalid: {
            color: '#fa755a',
            iconColor: '#fa755a'
        }
    };

    // Create an instance of the card Element.
    return elements.create('card', { style: stripeStyle, hidePostalCode: true });
}

const StripeCardInput = ({ element }: { element: stripe.elements.Element }) => {
    const mountPoint = useRef<HTMLDivElement>(null);

    useEffect(() => {
        element.mount(mountPoint.current!);
    }, []);

    return (
        <div ref={mountPoint}></div>
    )
}

const ToPayPreview = ({ selectedPlan, relevantProducts }: { selectedPlan: Plan, relevantProducts: RelevantProducts }) => {
    const t = useTranslation();
    const paidRightNow: [string, number][] = [];
    const renewInfo = [];
    if (selectedPlan.subscriptions.includes("membership")) {
        paidRightNow.push([t("summaries.membership_subscription.summary"), parseFloat(relevantProducts.membershipSubscriptionProduct.price)]);
        renewInfo.push(t("summaries.membership_subscription.renewal")(parseFloat(relevantProducts.membershipSubscriptionProduct.price)));
    }
    if (selectedPlan.subscriptions.includes("labaccess")) {
        if (!selectedPlan.products.includes(relevantProducts.starterPackProduct)) {
            // If the starter pack is included, the lab access subscription will start when the starter pack is over
            paidRightNow.push([t("summaries.labaccess_subscription.summary"), parseFloat(relevantProducts.labaccessSubscriptionProduct.price)]);
        }
        renewInfo.push(t("summaries.labaccess_subscription.renewal")(parseFloat(relevantProducts.labaccessSubscriptionProduct.price)));
    }
    for (const product of selectedPlan.products) {
        if (product === relevantProducts.starterPackProduct) {
            paidRightNow.push([t("summaries.starter_pack.summary"), parseFloat(product.price)]);
        } else if (product === relevantProducts.labaccessProduct) {
            paidRightNow.push([t("summaries.labaccess.summary"), parseFloat(product.price)]);
        } else {
            throw new Error("Unexpected product");
        }
    }
    if (renewInfo.length == 1) {
        renewInfo.push(t("summaries.renewal.one"));
    } else if (renewInfo.length > 1) {
        renewInfo.push(t("summaries.renewal.many"));
    }

    return (
        <>
            <span className="small-print">{t("summaries.payment_right_now")}</span>
            <div class="history-item to-pay-preview">
                <div class="receipt-items">
                    {paidRightNow.map(([name, price]) => (
                        <>
                            <span className="product-title">{name}</span>
                            <span className="receipt-item-amount">{price} {t("priceUnit")}</span>
                        </>
                    ))}
                </div>
                <div class="receipt-amount">
                    <span>{t("summaries.cart_total")}</span>
                    <span className="receipt-amount-value">{paidRightNow.reduce((s, [_, c]) => s + c, 0)} {t("priceUnit")}</span>
                </div>
            </div>
            {renewInfo.length > 0 ? (<span className="small-print">{renewInfo.join(" ")}</span>) : null}
        </>
    )
}
const Confirmation = ({ memberInfo, selectedPlan, relevantProducts, card, onRegistered, onBack }: { memberInfo: MemberInfo, selectedPlan: Plan, relevantProducts: RelevantProducts, card: stripe.elements.Element, onRegistered: (r: RegistrationSuccess) => void, onBack: ()=>void }) => {
    const t = useTranslation();
    const [inProgress, setInProgress] = useState(false);

    return (<>
        {/* <h2>{t("payment.title")}</h2> */}
        <div class="uk-flex-1" />
        <p>{t("payment.text")}</p>
        <div class="uk-flex-1" />
        <ToPayPreview selectedPlan={selectedPlan} relevantProducts={relevantProducts} />
        <div class="uk-flex-1" />
        <span class="payment-processor">{t("payment.payment_processor")}</span>
        <StripeCardInput element={card} />
        <button className="flow-button" disabled={inProgress} onClick={async () => {
            setInProgress(true);
            try {
                if (selectedPlan == null) {
                    throw new Error("No plan selected");
                }
                const paymentMethod = await createPaymentMethod(card, memberInfo);
                if (paymentMethod !== null) {
                    try {
                        onRegistered(await registerMember(paymentMethod, memberInfo, selectedPlan));
                    } catch (e) {
                        if (e instanceof PaymentFailedError) {
                            UIkit.modal.alert("<h2>Payment failed</h2>" + e.message);
                        } else {
                            throw e;
                        }
                    }
                }
            } finally {
                setInProgress(false);
            }
        }}>
            <span className={"uk-spinner uk-icon progress-spinner " + (inProgress ? "progress-spinner-visible" : "")} uk-spinner={''} />
            <span>{t("payment.pay")}</span>
        </button>
        <BackButton onClick={onBack} />
        <div class="uk-flex-1" />
    </>);
}

async function createPaymentMethod(element: stripe.elements.Element, memberInfo: MemberInfo): Promise<stripe.paymentMethod.PaymentMethod | null> {
    const result = await stripe.createPaymentMethod('card', element, {
        billing_details: {
            name: `${memberInfo.firstName} ${memberInfo.lastName}`,
            email: memberInfo.email,
            phone: memberInfo.phone,
            address: {
                postal_code: memberInfo.zipCode || undefined,
            },
        },
    });
    if (result.error) {
        UIkit.modal.alert("<h2>Your payment failed</h2>" + result.error.message);
        return null;
    }
    console.assert(result.paymentMethod !== undefined);
    return result.paymentMethod!;
}

enum RegisterResponseType {
    Success = "success",
    RequiresAction = "requires_action",
    Wait = "wait",
    Failed = "failed",
}

type RegisterResponse = {
    setup_intent_id: string
    type: RegisterResponseType
    token: string | null
    error: string | null
    action_info: PaymentAction | null
}

type SubscriptionType = "membership" | "labaccess"

type RegisterRequest = {
    purchase: Purchase
    setup_intent_id: string | null
    member: MemberInfo
    subscriptions: SubscriptionType[]
}

type RegistrationSuccess = {
    loginToken: string
}

async function registerMember(paymentMethod: stripe.paymentMethod.PaymentMethod, memberInfo: MemberInfo, selectedPlan: Plan): Promise<RegistrationSuccess> {
    const data: RegisterRequest = {
        member: memberInfo,
        purchase: {
            cart: selectedPlan.products.map(p => ({
                id: p.id,
                count: 1,
            })),
            // TODO: Should come from the same value that is displayed to the user
            expected_sum: "" + selectedPlan.products.reduce((sum, p) => sum + parseFloat(p.price), 0),
            stripe_payment_method_id: paymentMethod.id,
        },
        // All new members become subscribed to the yearly plan
        subscriptions: selectedPlan.subscriptions,
        setup_intent_id: null,
    };

    while (true) {
        let res: ServerResponse<RegisterResponse>;
        try {
            res = await common.ajax("POST", window.apiBasePath + "/webshop/register2", data);
        } catch (e: any) {
            if (e["message"] !== undefined) {
                throw new PaymentFailedError(e["message"]);
            } else {
                throw e;
            }
        }
        data.setup_intent_id = res.data.setup_intent_id;

        switch (res.data.type) {
            case RegisterResponseType.Success:
                return {
                    loginToken: res.data.token!
                };
            case RegisterResponseType.RequiresAction:
                if (res.data.action_info!.type === PaymentIntentNextActionType.USE_STRIPE_SDK) {
                    const stripeResult = await stripe.confirmCardSetup(res.data.action_info!.client_secret);
                    if (stripeResult.error) {
                        throw new PaymentFailedError(stripeResult.error.message!);
                    } else {
                        // The card action has been handled
                        // Now we try the server endpoint again
                    }
                } else {
                    throw new Error("Unexpected action type");
                }
                break;
            case RegisterResponseType.Wait:
                // Stripe needs some time to confirm the payment. Wait a bit and try again.
                await new Promise(resolve => setTimeout(resolve, 500));
            case RegisterResponseType.Failed:
                throw new PaymentFailedError(res.data.error!)
        }
    }
}

class PaymentFailedError {
    message: string;

    constructor(message: string) {
        this.message = message;
    }
}

type Product = {
    category_id: number,
    created_at: string,
    deleted_at: string | null,
    updated_at: string,
    description: string,
    display_order: number,
    filter: string,
    id: number,
    image_id: number | null,
    product_metadata: {
        subscription_type?: SubscriptionType,
        special_product_id?: string,
    },
    name: string,
    price: string,
    show: boolean,
    smallest_multiple: number,
    unit: string,
}

type RegisterPageData = {
    membershipProducts: {
        id: number,
        name: string,
        price: number,
    }[],
    productData: Product[],
    subscriptions: {

    }
}

const CheckIcon = ({ done }: { done: boolean }) => {
    return <span className={"uk-icon-small uk-icon task " + (done ? "task-done" : "")} uk-icon="icon: check"></span>
}

const Success = ({ member }: { member: member_t }) => {
    const [isBookModalOpen, setBookModalOpen] = useState(false);
    const [booked, setBooked] = useState(false);
    const [clickedSteps, setClickedSteps] = useState(new Set<number>());
    console.log("Rendering", clickedSteps);
    const t = useTranslation();

    useCalendlyEventListener({
        onEventScheduled: () => {
            setBooked(true);
        }
    })

    return (<>
        <h1>{t("success.title")}</h1>
        {t("success.text")}
        <ul className="registration-task-list">
            <li>
                <CheckIcon done={booked} />
                <div class="uk-flex uk-flex-column">
                    <span>{t("success.book_step")}</span>
                    <button className="flow-button flow-button-small" onClick={() => setBookModalOpen(true)}>{t("success.book_button")}</button>
                </div>
            </li>
            {t("success.steps").map((step, i) => <li key={i}><CheckIcon done={clickedSteps.has(i)} /><span>{step((e) => setClickedSteps(new Set(clickedSteps).add(i)))}</span></li>)}
        </ul>
        <div class="uk-flex-1" />
        <a href={RELATIVE_MEMBER_PORTAL} className="flow-button" >{t("success.continue_to_member_portal")}</a>
        <PopupModal
            url="https://calendly.com/medlemsintroduktion/medlemsintroduktion"
            rootElement={document.getElementById("root")!}
            open={isBookModalOpen}
            onModalClose={() => setBookModalOpen(false)}
            prefill={{
                name: member.firstname + " " + member.lastname,
                firstName: member.firstname,
                lastName: member.lastname,
                email: member.email,
            }}
        />
    </>);
}

const Discounts = ({ discounts, setDiscounts, onSubmit }: { discounts: DiscountsInfo, setDiscounts: (m: DiscountsInfo)=>void, onSubmit: ()=>void }) => {
    const t = useTranslation();

    const reasons: DiscountReason[] = ["student","unemployed","senior","other"];
    const [step, setStep] = useState(0);

    if (step == 0) {
        return <>
            <h2>{t("discounts.title")}</h2>
            <p>{t("discounts.text")}</p>

            {reasons.map(reason =>
                <>
                    <input type="checkbox" checked={discounts.discountReason === reason} onChange={(e) => setDiscounts({ ...discounts, discountReason: e.currentTarget.checked ? reason : null })} />
                    {t(`discounts.reasons.${reason}`)}
                </>
            )}
            <input type="text" placeholder={t("discounts.messagePlaceholder")} value={discounts.discountReasonMessage} onChange={(e) => setDiscounts({ ...discounts, discountReasonMessage: e.currentTarget.value })} />
            <button className="flow-button" onClick={() => setStep(1)} disabled={discounts.discountReason !== null && discounts.discountReasonMessage.length > 30}>{t("discounts.submit")}</button>
            <button className="flow-button" onClick={() => {
                setDiscounts({ discountReason: null, discountReasonMessage: "" });
                onSubmit();
            }}>{t("discounts.cancel")}</button>
        </>;
    } else {
        return <>
            <h2>{t("discounts.title")}</h2>
            {t("discounts.confirmation")}
            <button className="flow-button" onClick={onSubmit}>{t("discounts.submit")}</button>
            <button className="flow-button" onClick={() => {
                setDiscounts({ discountReason: null, discountReasonMessage: "" });
                onSubmit();
            }}>{t("discounts.cancel")}</button>
        </>
    }
}

const Calendar = ({ member }: { member: member_t }) => {
    const t = useTranslation();
    console.log(member);
    return (
        <>
            <h2>{t("calendar.title")}</h2>
            <p>{t("calendar.text")}</p>
            <PopupWidget
                url="https://calendly.com/medlemsintroduktion/medlemsintroduktion"
                text={t("calendar.book_button")}
                rootElement={document.getElementById("root")!}
                prefill={{
                    name: member.firstname + " " + member.lastname,
                    firstName: member.firstname,
                    lastName: member.lastname,
                    email: member.email,
                }}
            />
        </>
    )
}

const MakerspaceLogo = () => {
    return <img src={window.staticBasePath + "/images/logo-transparent-500px-300x210.png"} alt="Makerspace Logo" className="registration-logo" />
}

const heuristicallyPickLanguage = (): "en" | "sv" => {
    const langs = navigator.languages || [navigator.language];
    for (let lang of langs) {
        lang = lang.toLowerCase();

        if (lang.startsWith("sv")) {
            return "sv";
        } else if (lang.startsWith("en")) {
            return "en";
        }
    }

    // Fall back to English
    return "en";
}

type PlanId = "starterPack" | "makerspaceAccessSub" | "decideLater" | "singleMonth" | "discounted";

type RelevantProducts = {
    starterPackProduct: Product,
    baseMembershipProduct: Product,
    labaccessProduct: Product,
    membershipSubscriptionProduct: Product,
    labaccessSubscriptionProduct: Product,
}

const extractRelevantProducts = (products: Product[]): RelevantProducts => {
    const starterPackProduct = products.find(product => product.product_metadata.special_product_id === "access_starter_pack");
    const baseMembershipProduct = products.find(product => product.product_metadata.special_product_id === "single_membership_year");
    const labaccessProduct = products.find(product => product.product_metadata.special_product_id === "single_labaccess_month");
    const membershipSubscriptionProduct = products.find(product => product.product_metadata.subscription_type === "membership");
    const labaccessSubscriptionProduct = products.find(product => product.product_metadata.subscription_type === "labaccess");
    if (starterPackProduct === undefined) throw new Error("No starter pack product found");
    if (baseMembershipProduct === undefined) throw new Error("No base membership product found");
    if (labaccessProduct === undefined) throw new Error("No labaccess product found");
    if (membershipSubscriptionProduct === undefined) throw new Error("No membership subscription product found");
    if (labaccessSubscriptionProduct === undefined) throw new Error("No labaccess subscription product found");
    return {
        starterPackProduct,
        baseMembershipProduct,
        labaccessProduct,
        membershipSubscriptionProduct,
        labaccessSubscriptionProduct,
    };

}
const RegisterPage = ({ onChangeLanguage }: { onChangeLanguage: (lang: keyof typeof Translations) => void }) => {
    // Language chooser
    // Inspiration page?
    // Plan chooser
    // User details
    // Accept terms page
    // -> stripe
    // (Ideally calendar page)
    // Success page

    const [state, setState] = useState(State.ChoosePlan);
    const [selectedPlan, setSelectedPlan] = useState<PlanId | null>("starterPack"); // TODO: Should be null
    const [memberInfo, setMemberInfo] = useState<MemberInfo>({
        firstName: "",
        lastName: "",
        email: "",
        phone: "",
        zipCode: "",
    });
    const [acceptedTerms, setAcceptedTerms] = useState({
        accepted1: false,
        accepted2: false,
        accepted3: false
    });

    // TODO
    const [loggedInMember, setLoggedInMember] = useState<member_t | null>({
        address_street: "",
        address_extra: "",
        address_zipcode: "",
        address_city: "",
        email: "a.b@gmail.com",
        member_number: 1234,
        firstname: "Aron",
        lastname: "Granberg",
        phone: "0735986675",
        pin_code: "1234",
        labaccess_agreement_at: "2020-01-01",
    });
    const t = useTranslation();
    const card = createStripeCardInput();
    const [registerPageData, setRegisterPageData] = useState<RegisterPageData | null>(null);
    const [discounts, setDiscounts] = useState<DiscountsInfo>({
        discountReason: null,
        discountReasonMessage: "",
    });

    useEffect(() => {
        common.ajax('GET', `${window.apiBasePath}/webshop/register_page_data`).then(x => setRegisterPageData(x.data));
    }, []);

    if (registerPageData === null) {
        return <div>Loading...</div>
    }
    const relevantProducts = extractRelevantProducts(registerPageData.productData);
    const accessCostSingle = parseFloat(relevantProducts.labaccessProduct.price);
    const accessSubscriptionCost = parseFloat(relevantProducts.labaccessSubscriptionProduct.price);

    const plans: Plan[] = [
        {
            id: "singleMonth",
            title: t("plans.singleMonth.title"),
            abovePrice: t("plans.singleMonth.abovePrice"),
            price: parseFloat(relevantProducts.labaccessProduct.price),
            period: t("plans.singleMonth.period"),
            description: t("plans.singleMonth.description"),
            products: [relevantProducts.labaccessProduct],
            subscriptions: ["membership"],
            highlight: null,
        },
        {
            id: "starterPack",
            title: t("plans.starterPack.title"),
            abovePrice: t("plans.starterPack.abovePrice"),
            price: parseFloat(relevantProducts.starterPackProduct.price),
            period: t("plans.starterPack.period"),
            description: t("plans.starterPack.description"),
            products: [relevantProducts.starterPackProduct],
            subscriptions: ["membership"],
            highlight: "Recommended",
        },
        // {
        //     id: "makerspaceAccessSub",
        //     title: t("plans.makerspaceAccessSub.title"),
        //     abovePrice: t("plans.makerspaceAccessSub.abovePrice"),
        //     price: parseFloat(relevantProducts.labaccessSubscriptionProduct.price),
        //     period: t("plans.makerspaceAccessSub.period"),
        //     description: t("plans.makerspaceAccessSub.description"),
        //     products: [],
        //     subscriptions: ["membership", "labaccess"],
        //     highlight: null,
        // },
        {
            id: "decideLater",
            title: t("plans.decideLater.title"),
            abovePrice: t("plans.decideLater.abovePrice"),
            price: 0,
            period: t("plans.decideLater.period"),
            description: t("plans.decideLater.description")(accessCostSingle, accessSubscriptionCost),
            products: [],
            subscriptions: ["membership"],
            highlight: null,
        },
        // {
        //     id: "discounted",
        //     title: t("plans.discounted.title"),
        //     abovePrice: t("plans.discounted.abovePrice"),
        //     price: 0,
        //     period: t("plans.discounted.period"),
        //     description: t("plans.discounted.description"),
        //     products: [],
        //     subscriptions: ["membership"],
        //     highlight: null,
        // }
    ]

    const lowestMakerspaceAccessPrice = Math.min(accessCostSingle, accessSubscriptionCost);
    const highestMakerspaceAccessPrice = Math.max(accessCostSingle, accessSubscriptionCost);
    const activePlan = plans.find(plan => plan.id === selectedPlan);

    switch (state) {
        case State.ChooseLanguage:
            return <LanguageChooser setLanguage={lang => {
                onChangeLanguage(lang);
                setState(State.ChoosePlan);
            }} />;
        case State.ChoosePlan:
            return (<>
                <MakerspaceLogo />
                <h1>{t("memberships.title")}</h1>
                <p>{t("memberships.p1")}</p>
                <p>{t("memberships.p2")}</p>

                <Panel>
                    <h3>{t("baseMembership.title")}</h3>
                    <span className="small-price">{parseFloat(relevantProducts.baseMembershipProduct.price)} {t("priceUnit")} {t("baseMembership.period")}</span>
                    <ul>
                        {t("baseMembership.reasons").map((reason, i) => <li key={i}>{reason}</li>)}
                    </ul>
                    {/* <div className="price">
                        {parseFloat(relevantProducts.baseMembershipProduct.price)} {t("priceUnit")}
                        <span className="period">{t("baseMembership.period")}</span>
                    </div> */}
                    <span className="panel-divider" />
                    <h3>{t("makerspaceAccess.title")}</h3>
                    <span className="small-price">
                        {lowestMakerspaceAccessPrice != highestMakerspaceAccessPrice ? `${lowestMakerspaceAccessPrice}-${highestMakerspaceAccessPrice}${t("makerspaceAccess.price")}`
                            : `${lowestMakerspaceAccessPrice}${t("makerspaceAccess.price")}`
                        }
                    </span>
                    <span className="requirement">{t("makerspaceAccess.requirement")}</span>
                    <ul>
                        {t("makerspaceAccess.reasons").map((reason, i) => <li key={i}>{reason}</li>)}
                    </ul>
                </Panel>
                <h2>{t("chooseYourPlan.title")}</h2>
                <span>{t("chooseYourPlan.help")}</span>
                {plans.map(plan => <PlanButton selected={selectedPlan === plan.id} onClick={() => setSelectedPlan(plan.id)} plan={plan} />)}
                <button className="flow-button" onClick={() => setState(State.Discounts)}>{t("apply_for_discounts")}</button>
                {activePlan !== undefined ? <ToPayPreview selectedPlan={activePlan} relevantProducts={relevantProducts}  /> : null}
                <button className="flow-button" disabled={selectedPlan == null} onClick={() => setState(State.MemberInfo)}>{t("continue")}</button>
            </>);
        case State.MemberInfo:
            return (<>
                <MakerspaceLogo />
                <h2>{t("memberInfo.title")}</h2>
                <MemberInfoForm info={memberInfo} onChange={setMemberInfo} onSubmit={(_) => setState(State.Terms)} onBack={() => setState(State.ChoosePlan)} />
            </>);
        case State.Terms:
            return (<>
                <MakerspaceLogo />
                <TermsAndConditions onAccept={() => setState(State.Confirmation)} onBack={() => setState(State.MemberInfo)} acceptedTerms={acceptedTerms} onChangeAcceptedTerms={setAcceptedTerms} />
            </>);
        case State.Calendar:
            // TODO: Should get member info from server, as it has been validated there
            if (loggedInMember === null) throw new Error("No logged in member");

            return (<>
                <MakerspaceLogo />
                <Calendar member={loggedInMember} />
            </>);
        case State.Confirmation:
            if (activePlan === undefined) throw new Error("No active plan");
            return <>
                <MakerspaceLogo />
                <Confirmation
                    card={card}
                    selectedPlan={activePlan}
                    memberInfo={memberInfo}
                    relevantProducts={relevantProducts}
                    onRegistered={async (r) => {
                        common.login(r.loginToken);
                        setLoggedInMember(await LoadCurrentMemberInfo());
                        setState(State.Success);
                    }}
                    onBack={() => setState(State.Terms)}
                />
            </>;
        case State.Success:
            if (loggedInMember === null) throw new Error("No logged in member");

            return <>
                <MakerspaceLogo />
                <Success member={loggedInMember} />
            </>;
        case State.Discounts:
            return <>
                <MakerspaceLogo />
                <Discounts discounts={discounts} setDiscounts={setDiscounts} onSubmit={() => {
                    if (discounts.discountReason !== null) {
                        setSelectedPlan("discounted");
                    }
                    setState(State.ChoosePlan);
                }} />
            </>
    }
}

const TranslationWrapper = () => {
    const [language, setLanguage] = useState<keyof typeof Translations>(heuristicallyPickLanguage());
    const tr: Dictionary = new Translation(Translations[language]);

    return (
        <TranslationContext.Provider value={tr}>
            <div className="content-wrapper">
                <RegisterPage onChangeLanguage={setLanguage} />
            </div>
        </TranslationContext.Provider>
    )
}

common.documentLoaded().then(() => {
    const root = document.getElementById('root');
    if (root != null) {
        render(
            <TranslationWrapper />,
            root
        );
    }
});
