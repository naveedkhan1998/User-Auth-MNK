const tax_rate = prompt("Enter tax rate (0.10)");
const shipping_threshold = prompt("Enter shipping threshold (1000)");

/* add loop and other code here ... in this simple exercise we are not
   going to concern ourselves with minimizing globals, etc */
   document.write('<table class="table-fill">');
   document.write("<thead>");
   document.write("<tr>");
   document.write('<th colspan="2">Product</th>');
   document.write("<th>#</th>");
   document.write("<th>Price</th>");
   document.write("<th>Amount</th>");
   document.write("</tr>");
   document.write("</thead>");
   document.write('<tbody id="cart-items">');
   
   let subTotal = 0

   for (let i = 0; i < cart.length; i++) {
     const item = cart[i];
     const total = calculateTotal(item.quantity,item.product.price);
     subTotal += total
     outputCartRow(item, total);
   }
   
   document.write(`<tr class="totals">`);
   document.write("<td colspan='4'>Subtotal</td>");
   document.write(`<td>$${subTotal.toFixed(2)}</td>`);
   document.write("</tr>");
   document.write(`<tr class="totals">`);
   document.write("<td colspan='4'>Tax</td>");
   document.write(`<td>$${(tax_rate * subTotal).toFixed(2)}</td>`);
   document.write("</tr>");
   
   const shippingCost = shipping_threshold && subTotal  < shipping_threshold ? 40.00 : 0.00;
   document.write(`<tr class="totals">`);
   document.write("<td colspan='4'>Shipping</td>");
   document.write(`<td>$${shippingCost.toFixed(2)}</td>`);
   document.write("</tr>");

   const grandTotal = subTotal  + (tax_rate * subTotal) + shippingCost;
   document.write(`<tr class="totals">`);
   document.write("<td colspan='4' class='focus'>Grand Total</td>");
   document.write(`<td class='focus'>$${grandTotal.toFixed(2)}</td>`);
   document.write("</tr>");
   
   document.write("</tbody>");
   document.write("</table>");
   