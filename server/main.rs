use std::net::{Ipv4Addr, TcpStream, TcpListener, Shutdown, SocketAddrV4};
use std::io;
// fn handle_client(stream: TcpStream) {
// 	print!("new connection!");
//     // ...
// }

fn main() -> io::Result<()> {
    let listener = TcpListener::bind("127.0.0.1:12222")?;

    // accept connections and process them serially
    for stream in listener.incoming() {
        // handle_client(stream?);
        match stream {
        Ok(stream) => {
            println!("new client!");
        }
        Err(e) => { /* connection failed */ }
    }
    }
    Ok(())
}