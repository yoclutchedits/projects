const gridEl = document.querySelector(".grid")
for (let row = 0; row < 8; row++) {
    for (let col =0 ; col<8; col++){
        const square = document.createElement("div")
        if ((row+col) % 2 == 0){
            square.classList.add("white");
        }
        else{
            square.classList.add("black");
        }
        gridEl.appendChild(square)
    }
}
async function loadBoard() {
let response= await fetch("http://127.0.0.1:8000/api/board")
const data = await response.json()
console.log(response)
console.log(data)
 }

loadBoard();