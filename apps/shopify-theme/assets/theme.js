/* SCHLUESSELKINDER — minimal client-side glue.
 * No framework. No build step. ES modules avoided so this works as a single tag.
 */
(function () {
  "use strict";

  // ---------- Cart drawer ----------
  var cartDrawer = document.querySelector("[data-cart-drawer]");
  var cartCountEls = document.querySelectorAll("[data-cart-count]");
  var openers = document.querySelectorAll("[data-cart-open]");
  var closers = document.querySelectorAll("[data-cart-close]");

  function openCart() {
    if (!cartDrawer) return;
    cartDrawer.setAttribute("aria-hidden", "false");
    document.documentElement.style.overflow = "hidden";
    refreshCart();
  }

  function closeCart() {
    if (!cartDrawer) return;
    cartDrawer.setAttribute("aria-hidden", "true");
    document.documentElement.style.overflow = "";
  }

  openers.forEach(function (b) { b.addEventListener("click", function (e) { e.preventDefault(); openCart(); }); });
  closers.forEach(function (b) { b.addEventListener("click", function (e) { e.preventDefault(); closeCart(); }); });

  if (cartDrawer) {
    var backdrop = cartDrawer.querySelector("[data-cart-backdrop]");
    if (backdrop) backdrop.addEventListener("click", closeCart);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && cartDrawer.getAttribute("aria-hidden") === "false") closeCart();
    });
  }

  function setCartCount(count) {
    cartCountEls.forEach(function (el) {
      el.setAttribute("data-count", String(count));
      el.textContent = count > 0 ? count : "";
    });
  }

  function refreshCart() {
    fetch("/cart.js", { headers: { Accept: "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (cart) {
        setCartCount(cart.item_count);
        renderCartLines(cart);
      })
      .catch(function () { /* silent — keep DOM as-is */ });
  }

  function renderCartLines(cart) {
    if (!cartDrawer) return;
    var list = cartDrawer.querySelector("[data-cart-items]");
    var subtotal = cartDrawer.querySelector("[data-cart-subtotal]");
    if (!list) return;
    if (!cart.items || cart.items.length === 0) {
      list.innerHTML = '<p class="meta">{{ "cart.empty" }}</p>';
      if (subtotal) subtotal.textContent = "";
      return;
    }
    var html = cart.items.map(function (item) {
      var img = item.image ? '<img src="' + item.image + '" alt="">' : "";
      return (
        '<div class="cart-line" data-line-key="' + item.key + '">' +
          '<div class="cart-line__media">' + img + "</div>" +
          '<div class="cart-line__body">' +
            '<div class="cart-line__title">' + item.product_title + "</div>" +
            '<div class="meta">' + item.variant_title + " · " + item.quantity + "×</div>" +
          "</div>" +
          '<div class="cart-line__price price">' + formatMoney(item.final_line_price) + "</div>" +
        "</div>"
      );
    }).join("");
    list.innerHTML = html;
    if (subtotal) subtotal.textContent = formatMoney(cart.total_price);
  }

  function formatMoney(cents) {
    var euros = (cents / 100).toFixed(2).replace(".", ",");
    return euros + " €";
  }

  // ---------- Add to cart (works on product page + cards) ----------
  document.addEventListener("submit", function (e) {
    var form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (form.getAttribute("action") !== "/cart/add") return;
    e.preventDefault();
    var fd = new FormData(form);
    var btn = form.querySelector('[type="submit"]');
    if (btn) btn.setAttribute("aria-disabled", "true");
    fetch("/cart/add.js", {
      method: "POST",
      headers: { Accept: "application/json" },
      body: fd,
    })
      .then(function (r) { return r.json(); })
      .then(function () { openCart(); })
      .catch(function () {})
      .finally(function () { if (btn) btn.removeAttribute("aria-disabled"); });
  });

  // ---------- Mobile nav ----------
  var mobileNav = document.querySelector("[data-mobile-nav]");
  document.querySelectorAll("[data-mobile-nav-open]").forEach(function (b) {
    b.addEventListener("click", function () {
      if (mobileNav) {
        mobileNav.setAttribute("aria-hidden", "false");
        document.documentElement.style.overflow = "hidden";
      }
    });
  });
  document.querySelectorAll("[data-mobile-nav-close]").forEach(function (b) {
    b.addEventListener("click", function () {
      if (mobileNav) {
        mobileNav.setAttribute("aria-hidden", "true");
        document.documentElement.style.overflow = "";
      }
    });
  });

  // ---------- Variant picker ----------
  document.querySelectorAll("[data-variant-form]").forEach(function (form) {
    var options = form.querySelectorAll("[data-variant-option]");
    options.forEach(function (opt) {
      opt.addEventListener("click", function () {
        var name = opt.getAttribute("data-option-name");
        form.querySelectorAll('[data-variant-option][data-option-name="' + name + '"]').forEach(function (o) {
          o.setAttribute("aria-checked", o === opt ? "true" : "false");
        });
        updateVariantId(form);
      });
    });
    updateVariantId(form);
  });

  function updateVariantId(form) {
    var idInput = form.querySelector('[name="id"]');
    var variantsData = form.getAttribute("data-variants");
    if (!idInput || !variantsData) return;
    var variants = JSON.parse(variantsData);
    var selected = {};
    form.querySelectorAll('[data-variant-option][aria-checked="true"]').forEach(function (o) {
      selected[o.getAttribute("data-option-name")] = o.getAttribute("data-option-value");
    });
    var match = variants.find(function (v) {
      return Object.keys(selected).every(function (k, i) { return v.options[i] === selected[k]; });
    });
    if (match) {
      idInput.value = match.id;
      var priceEl = form.querySelector("[data-variant-price]");
      if (priceEl) priceEl.textContent = formatMoney(match.price);
      var sub = form.querySelector('[type="submit"]');
      if (sub) sub.toggleAttribute("aria-disabled", !match.available);
    }
  }

  // Initial cart count load
  refreshCart();
})();
