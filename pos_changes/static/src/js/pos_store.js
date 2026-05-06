// /** @odoo-module **/
// import { PosStore } from "@point_of_sale/app/services/pos_store";
// import { patch } from "@web/core/utils/patch";

// patch(PosStore.prototype, {
//     async setup() {
//         await super.setup(...arguments);

//         const rawQuants = this.models['stock.quant'].getAll();
//         const allLocations = this.models['stock.location'].getAll();

//         // લોકેશનને ઝડપથી શોધવા માટે એક Map બનાવીએ
//         const locationMap = Object.fromEntries(
//             allLocations.map(loc => [loc.id, loc.complete_name || loc.name])
//         );

//         console.log(`--- Total Records Found: ${rawQuants.length} ---`);

//         rawQuants.forEach((quant) => {
//             if (quant && quant.product_id && quant.location_id) {
                
//                 const pId = quant.product_id.id || quant.product_id;
                
//                 // અહીં આપણે Map માંથી પૂરું નામ મેળવીશું
//                 const locId = quant.location_id.id || quant.location_id;
//                 const locName = locationMap[locId] || "Location Name Not Found";
                
//                 const qty = quant.quantity || 0;

//                 console.log(`Product: ${pId} | Location: ${locName} | Qty: ${qty}`);
//             }
//         });
//     }
// });
// ----------------------------------------------------------------------------------------------------

// /** @odoo-module **/
// import { PosStore } from "@point_of_sale/app/services/pos_store";
// import { patch } from "@web/core/utils/patch";

// patch(PosStore.prototype, {
//     async setup() {
//         await super.setup(...arguments);

//         const rawQuants = this.models['stock.quant'].getAll();
//         const allLocations = this.models['stock.location'].getAll();

//         const locationMap = Object.fromEntries(
//             allLocations.map(loc => [loc.id, loc.complete_name || loc.name])
//         );

//         // આ Map માં આપણે સ્ટોક સેવ કરીશું
//         this.productStockMap = {};

//         rawQuants.forEach((quant) => {
//             if (quant && quant.product_id && quant.location_id) {
//                 const pId = quant.product_id.id || quant.product_id;
//                 const locId = quant.location_id.id || quant.location_id;
//                 const locName = locationMap[locId] || "Unknown Location";
//                 const qty = quant.quantity || 0;

//                 if (!this.productStockMap[pId]) {
//                     this.productStockMap[pId] = [];
//                 }

//                 // પ્રોડક્ટ આઈડી મુજબ ડેટા પુશ કરો
//                 this.productStockMap[pId].push({
//                     locationName: locName,
//                     stockQty: qty
//                 });
//             }
//         });
//         console.log("Stock Map Initialized:", this.productStockMap);
//     }
// });


/** @odoo-module **/
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async setup() {
        // Essential: Call the original setup first to load models
        await super.setup(...arguments);

        const rawQuants = this.models['stock.quant'].getAll();
        const allLocations = this.models['stock.location'].getAll();

        // Create a lookup map for Location names
        const locationMap = Object.fromEntries(
            allLocations.map(loc => [loc.id, loc.complete_name || loc.name])
        );

        // Initialize the map on 'this' so it's accessible throughout the POS
        this.productStockMap = {};

        console.log(`--- Processing ${rawQuants.length} Stock Records ---`);

        rawQuants.forEach((quant) => {
            if (quant && quant.product_id && quant.location_id) {
                // Handle both object and ID formats for product/location
                const pId = quant.product_id.id || quant.product_id;
                const locId = quant.location_id.id || quant.location_id;
                
                const locName = locationMap[locId] || "Unknown Location";
                const qty = quant.quantity || 0;

                // 1. Log to console as per your requirement
                console.log(`Product: ${pId} | Location: ${locName} | Qty: ${qty}`);

                // 2. Store in the map for other functionalities
                if (!this.productStockMap[pId]) {
                    this.productStockMap[pId] = [];
                }

                this.productStockMap[pId].push({
                    locationName: locName,
                    stockQty: qty
                });
            }
        });

        // જૂની લાઇન: console.log("Stock Map Ready:", this.productStockMap);

        // નવી લાઇન (જેનાથી તમને જોઈએ એવું Format દેખાશે):
        console.log("Stock Map Ready:", JSON.parse(JSON.stringify(this.productStockMap)));
    }
});