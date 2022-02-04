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
        public static bool connected = false;
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
                connected = true;
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
            while (connected)
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
            while (connected)
            {
                try
                {
                    byte[] data = new byte[256];
                    string message = string.Empty;

                    int bytes = stream.Read(data, 0, data.Length);
                    message = Encoding.UTF8.GetString(data, 0, bytes);
                    if (!string.IsNullOrEmpty(message))
                    {
                        string command = message[0] + "" + message[1] + "" + message[2];
                        if (command == "req")
                        {
                            string action = message[4] + "" + message[5] + "" + message[6];
                            if (action == "acc")
                            {
                                sendMessage(acc);
                            }
                            else if (message == "quit")
                            {
                                Console.WriteLine("Successfuly disconnected");
                                client.Close();
                                connected = false;
                                return;
                            }
                            else if (action == "loa") //load gameplay scene
                            {
                                Console.WriteLine("Load gameplay scene!");
                                //ucitaj scenu
                                sendMessage("/ca");
                            }
                            else if (action == "spa") //spawn players
                            {
                                string[] helper = message.Split(':');
                                string[] playerNames = helper[1].Split(',');
                                Console.WriteLine("Spawn players:" + helper[1]);
                                sendMessage("/ca");
                            }
                            else if (action == "add") //add boxes
                            {
                                string[] helper = message.Split(':');
                                string[] amonut = helper[1].Split(',');
                                Console.WriteLine("Add boxes:" + helper[1]);
                                sendMessage("/ca");
                            }
                            else if (action == "rem") //remove boxes
                            {
                                string[] helper = message.Split(':');
                                string[] amonut = helper[1].Split(',');
                                Console.WriteLine("Remove boxes:" + helper[1]);
                                sendMessage("/ca");
                            }
                            else if (action == "sho") // show question
                            {
                                string[] helper = message.Split(':');
                                //helper[1] contains question
                                Console.WriteLine("Question: " + helper[1]);
                            }
                            else if (action == "die")
                            {
                                string[] helper = message.Split(':');
                                string[] amonut = helper[1].Split(',');
                                Console.WriteLine($"You lost!\nAdd coins:{amonut[0]}\nDeduce points:{amonut[1]}");
                            }
                            else if (action == "win")
                            {
                                string[] helper = message.Split(':');
                                string[] amonut = helper[1].Split(',');
                                Console.WriteLine($"You won!\nAdd coins:{amonut[0]}\nDeduce points:{amonut[1]}");
                            }
                            else
                                Console.WriteLine("Undetected action for command request!");
                        }
                        else if (command == "err")
                        {
                            string action = message[4] + "" + message[5] + "" + message[6];
                            if (action == "cre") //wrong credentials
                            {
                                Console.WriteLine("Wrong credentials!");
                                connected = false;
                                client.Close();
                                return;
                            }
                            else
                                Console.WriteLine("Undetected action for command error!");
                        }
                        else if (command == "inf")
                            Console.WriteLine(message);
                        else
                            Console.WriteLine("Undetected command!");
                    }

                }
                catch
                {
                    Console.WriteLine("An error occured!");
                    connected = false;
                    client.Close();
                    return;
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
