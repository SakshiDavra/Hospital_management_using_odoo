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

        await super.setup(...arguments);

        const rawQuants = this.models['stock.quant'].getAll();
        const allLocations = this.models['stock.location'].getAll();


        const locationMap = Object.fromEntries(
            allLocations.map(loc => [loc.id, loc.complete_name || loc.name])
        );

        this.productStockMap = {};

        console.log(`--- Processing ${rawQuants.length} Stock Records ---`);

        rawQuants.forEach((quant) => {
            if (quant && quant.product_id && quant.location_id) {
                const pId = quant.product_id.id || quant.product_id;
                const locId = quant.location_id.id || quant.location_id;
                const locName = locationMap[locId] || "Unknown Location";
                const qty = quant.quantity || 0;

                if (!this.productStockMap[pId]) {
                    this.productStockMap[pId] = [];
                }


                const existingLoc = this.productStockMap[pId].find(s => s.locationId === locId);
                
                if (existingLoc) {
                    existingLoc.stockQty += qty;
                } else {

                    this.productStockMap[pId].push({
                        locationId: locId,
                        locationName: locName,
                        stockQty: qty
                    });
                }
            }
        });
        console.log("Stock Map Ready:", JSON.parse(JSON.stringify(this.productStockMap)));
    }
});