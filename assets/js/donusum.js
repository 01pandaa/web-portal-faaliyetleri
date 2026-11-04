/*
 * Web Portal Faaliyetleri — Google Ads dönüşüm takibi (telefon + WhatsApp tıklamaları)
 *
 * Tüm sayfalarda tel: ve wa.me / WhatsApp bağlantılarına yapılan tıklamaları
 * Google Ads dönüşümü olarak gönderir. Etiketler yalnızca bu dosyada tutulur;
 * yeni bir dönüşüm etiketi alındığında sadece aşağıdaki DONUSUMLER listesini güncelleyin.
 *
 * Etiket nereden alınır?
 * Google Ads > Hedefler > Dönüşümler > Özet > + Yeni dönüşüm işlemi > Web sitesi >
 * "Manuel olarak kod kullanarak dönüşüm işlemi ekle" > Etkinlik snippet'indeki
 * send_to değeri: 'AW-XXXXXXXXXX/ETIKET'
 */
(function () {
  'use strict';

  var DONUSUMLER = {
    // Telefon numarasına tıklama
    telefon: [
      'AW-18537615740/-ntTCPKy7rEdEPyitodF' // Tıkla ve ara
    ],
    // WhatsApp butonuna tıklama
    whatsapp: [
      'AW-18537615740/Dx5mCKr56LEdEPyitodF' // Kişi (WhatsApp tıklaması)
    ]
  };

  window.dataLayer = window.dataLayer || [];
  if (typeof window.gtag !== 'function') {
    window.gtag = function () { window.dataLayer.push(arguments); };
  }

  // Etiketi olan her hesap için config çağrısı (send_to'nun çalışması için gerekli)
  var hesaplar = {};
  Object.keys(DONUSUMLER).forEach(function (tur) {
    DONUSUMLER[tur].forEach(function (s) { hesaplar[s.split('/')[0]] = true; });
  });
  Object.keys(hesaplar).forEach(function (id) { window.gtag('config', id); });

  var sonGonderim = 0;

  function gonder(tur, href) {
    var simdi = Date.now();
    if (simdi - sonGonderim < 1500) return; // çift tıklamayı tek say
    sonGonderim = simdi;
    DONUSUMLER[tur].forEach(function (sendTo) {
      window.gtag('event', 'conversion', {
        send_to: sendTo,
        value: 1.0,
        currency: 'TRY',
        transport_type: 'beacon'
      });
    });
    window.gtag('event', tur === 'telefon' ? 'telefon_tiklama' : 'whatsapp_tiklama', {
      link_url: href,
      sayfa: location.pathname
    });
  }

  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (/^tel:/i.test(href)) {
      gonder('telefon', href);
    } else if (/(wa\.me\/|api\.whatsapp\.com|web\.whatsapp\.com|whatsapp:\/\/)/i.test(href)) {
      gonder('whatsapp', href);
    }
  }, true);
})();
