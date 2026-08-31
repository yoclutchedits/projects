const gridEl = document.querySelector(".grid")
const squareEls =Array.from({length: 8}, () => Array(8).fill(null))
for (let row = 0; row < 8; row++) {
    for (let col =0 ; col<8; col++){
        const square = document.createElement("div")
        if ((row+col) % 2 == 0){
            square.classList.add("white");
        }
        else{
            square.classList.add("black");
        }
        squareEls[row][col] = square;
        gridEl.appendChild(square)
    }
}
function renderBoard(board) {
    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const piece = board[row][col];        
            const squareEl = squareEls[row][col];      

            if (piece) {
                squareEl.style.backgroundImage = "url('pieces/" + piece + ".png')";
            } else {
                squareEl.style.backgroundImage = "";
            }
        }
    }
}

async function loadBoard() {
let response= await fetch("http://127.0.0.1:8000/api/board")
const data = await response.json()
renderBoard(data.board);
 }

loadBoard();