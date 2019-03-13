/// <reference path="../node_modules/@types/stripe-v3/index.d.ts" />
import Cart from "./cart"
import * as common from "./common"
import {login} from "./common";
declare var UIkit: any;


common.onGetAndDocumentLoaded("/webshop/register_page_data", (value: any) => {
    common.addSidebarListeners();

    const {productData, membershipProducts} = value;

  // Create a Stripe client.
  const stripe = Stripe(window.stripeKey);
  const apiBasePath = window.apiBasePath;

  // Create an instance of Elements.
  const elements = stripe.elements({ locale: "sv" });

    // Add membership products
    membershipProducts.forEach((product: any) => {
        document.querySelector("#products").innerHTML += `<div><input class="uk-radio" type="radio" value="${product.id}" name="product" checked/> ${product.name}: ${product.price} kr</div>`;
    });

  // Custom styling can be passed to options when creating an Element.
  // (Note that this demo uses a wider set of styles than the guide below.)
  const style = {
    base: {
      color: '#32325d',
      lineHeight: '18px',
      fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
      fontSmoothing: 'antialiased',
      fontSize: '16px',
      '::placeholder': {
        color: '#8a8f94'
      }
    },
    invalid: {
      color: '#fa755a',
      iconColor: '#fa755a'
    }
  };

  // Create an instance of the card Element.
  const card = elements.create('card', {style: style});

  // Add an instance of the card Element into the `card-element` <div>.
  card.mount('#card-element');

  // Used to prevent clicking the 'Pay' button twice
  const duplicatePurchaseRand = (100000000*Math.random())|0;

  const id2item = new Map();

  for (const cat of productData) {
    for (const item of cat.items) {
      id2item.set(item.id, item);
    }
  }

  let cart : Cart = new Cart([]);

  function refresh() {
    let checked = document.querySelectorAll(".uk-radio:checked");

    // Should only have 1 checked radio button
    if (checked.length !== 1) throw new Error("expected one checked radio button was " + checked.length);

    cart = new Cart([{
      id: Number((<HTMLInputElement>checked[0]).value),
      count: 1,
    }]);

    const totalSum = cart.sum(id2item);
    document.querySelector("#pay-button").querySelector("span").innerHTML = "Betala " + Cart.formatCurrency(totalSum);
  }

  [].forEach.call(document.querySelectorAll(".uk-radio"), (el: HTMLElement) => {
    el.addEventListener("change", ev => {
      refresh();
    });
    el.addEventListener("input", ev => {
      refresh();
    });
  });

  let waitingForPaymentResponse = false;
  document.querySelector("#pay-button").addEventListener("click", ev => {
    ev.preventDefault();

    // Don't allow any clicks while waiting for a response from the server
    if (waitingForPaymentResponse) {
      return;
    }

    waitingForPaymentResponse = true;

    const spinner = document.querySelector(".progress-spinner");
    spinner.classList.add("progress-spinner-visible");
    let errorElement = document.getElementById('card-errors');
    errorElement.textContent = "";

    stripe.createSource(card).then(function(result) {
      if (result.error) {
        spinner.classList.remove("progress-spinner-visible");
        // Inform the user if there was an error.
        errorElement.textContent = result.error.message;
        waitingForPaymentResponse = false;
      } else {
        common.ajax("POST", apiBasePath + "/webshop/register", {
            member: {
              firstname: common.getValue("#firstname"),
              lastname: common.getValue("#lastname"),
              email: common.getValue("#email"),
              phone: common.getValue("#phone"),
              address_street: "", // common.getValue("#address_street"),
              address_extra: "", // common.getValue("#address_extra"),
              address_zipcode: common.getValue("#address_zipcode"),
              address_city: "", // common.getValue("#address_city"),
            },
            purchase: {
              cart: cart.items,
              expectedSum: cart.sum(id2item),
              stripeSource: result.source.id,
              stripeThreeDSecure: result.source.card.three_d_secure,
              duplicatePurchaseRand: duplicatePurchaseRand,
            }
          }).then(json => {
            spinner.classList.remove("progress-spinner-visible");
            waitingForPaymentResponse = false;
            const token :string = json.data.token;
            if (token) {
                login(token);
            }
            if (json.data.redirect) {
              window.location.href = json.data.redirect;
            } else {
              window.location.href = "receipt/" + json.data.transaction_id;
            }
          }).catch(json => {
            spinner.classList.remove("progress-spinner-visible");
            waitingForPaymentResponse = false;
            if (json.what === "not_unique") {
              UIkit.modal.alert("<h2>Register failed</h2>A member with this email is already registred");
            } else {
              UIkit.modal.alert("<h2>The playment failed</h2>" + common.get_error(json));
            }
          }
        );
      }
    });
  });

  refresh();
});