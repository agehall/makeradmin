import * as common from "./common"
import { formatDateTime, UNAUTHORIZED } from "./common";
import { render_login } from "./login";
declare var UIkit: any;

common.documentLoaded().then(() => {
    common.addSidebarListeners();

    const content = document.getElementById("receipt-content")!;

    function pending() {
        content.innerHTML = `<h1>Din betalning har inte bekräftats ännu. Var god vänta.</h1>`;
        setTimeout(update, 3000);
    }

    function failed() {
        content.innerHTML = `<h1>Din betalning misslyckades</h1>`;
    }

    function showLogin() {
        render_login(content, "Logga in för att se kvittot", '/shop/receipt/' + window.transactionId);
    }

    function completed(cart: any, transaction: any, member: any) {
        let cartHtml = transaction.contents.map((item: any) => {
            return `
                <a class="product-title" href="/shop/product/${item.product.id}">${item.product.name}</a>
                <span class="receipt-item-count">${item.count} ${item.product.unit}</span>
                <span class="receipt-item-amount">${item.amount} kr</span>
            `;
        }).join("");

        const createdAt = formatDateTime(transaction.created_at);

        content.innerHTML = `
            <h1>Tack för ditt köp!</h1>
            <div class="history-item history-item-${transaction.status}">
                <span class="receipt-id receipt-header">
                    <span>Kvitto ${transaction.id}</span>
                    <span class="receipt-date">${createdAt}</span>
                </span>
                <div class="receipt-items">
                    ${cartHtml}
                </div>
                <div class="receipt-amount">
                    <span>Summa</span>
                    <span class="receipt-amount-value">${transaction.amount} kr</span>
                </div>
                <div class="receipt-items">
                    <span class="product-title">Medlem</span>
                    <span class="receipt-item-amount" style="min-width: 200px;">${member.firstname} ${member.lastname} #${member.member_number}</span>
                </div>
            </div>
            <div class="receipt-message">
                <p>Ett kvitto har också skickats via email.</p>
                <p>Stockholm Makerspace - Drottning Kristinas väg 53, 114 28 Stockholm</p>
            </div>
        `;
    }

    function update() {
        content.innerHTML = '';
        common
            .ajax("GET", window.apiBasePath + "/webshop/member/current/receipt/" + window.transactionId, {})
            .then(json => {
                let { cart, transaction, member } = json.data;
                if (transaction.status === "failed") {
                    failed();
                } else if (transaction.status === "completed") {
                    completed(cart, transaction, member);
                }
                else {
                    pending();
                }
            })
            .catch(json => {
                if (json.status === UNAUTHORIZED) {
                    showLogin();
                }
                else {
                    pending();
                }
            });
    }

    update();
});
