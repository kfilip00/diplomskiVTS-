using System;
using System.IO;
using System.Net.Sockets;
using System.Text;
using System.Threading;

namespace CSharpSocketsV2
{
    class Program
    {
        public static TcpClient client;
        public static string acc;
        public string getAcc()
        {
            while (true)
            {
                string email, password, nick;
                Console.Write("Do you have account? (Y/N): ");
                string answer = Console.ReadLine().ToLower();
                if (answer == "yes" || answer == "y")
                {
                    Console.Write("email: ");
                    email = Console.ReadLine();
                    Console.Write("password: ");
                    password = Console.ReadLine();
                    return $"/log,{email},{password}";
                }
                else if (answer == "no" || answer == "n")
                {
                    Console.Write("nick: ");
                    nick = Console.ReadLine();
                    Console.Write("email: ");
                    email = Console.ReadLine();
                    Console.Write("password: ");
                    password = Console.ReadLine();
                    return $"/log,{email},{password},{nick}";

                }
            }
        }
        public void ExecuteClient()
        {
            connection:
            try
            {
                TcpClient _client = new TcpClient("127.0.0.1", 5000);
                client = _client;
                Thread handle_receive = new Thread(() => getMessage());
                handle_receive.Start();
                Thread handle_send = new Thread(() => sendMessage());
                handle_send.Start();

            }
            catch (Exception e)
            {
                Console.WriteLine("An error occured...");
                goto connection;
            }
        }
        public static void sendMessage()
        {
            
            while (true)
            {
                string message = Console.ReadLine();
                sendMessage(message);
            }
        }
        public static void sendMessage(string message)
        {
            NetworkStream stream = client.GetStream();
            byte[] sendData = Encoding.UTF8.GetBytes(message);
            stream.Write(sendData, 0, sendData.Length);
        }
        public static void getMessage()
        {
            NetworkStream stream = client.GetStream();
            //StreamReader sr = new StreamReader(stream);
            while (true)
            {
                byte[] data = new byte[256];
                string message = string.Empty;

                int bytes = stream.Read(data, 0, data.Length);
                message = Encoding.UTF8.GetString(data, 0, bytes);
                if(!string.IsNullOrEmpty(message))
                {
                    string command = message[0]+""+message[1]+""+message[2];
                    if (command=="req")
                    {
                        string action = string.Empty;
                        for (int i = 4; i < message.Length; i++)
                        {
                            action += message[i];
                        }
                        if (action=="acc")
                        {
                            sendMessage(acc);
                        }
                    }
                    else
                        Console.WriteLine(message);
                }

            }
        }
        static void Main(string[] args)
        {
            Program p = new Program();
            acc = p.getAcc();
            p.ExecuteClient();
        }
       
    }
}
