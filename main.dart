import 'package:flutter/material.dart';
import 'package:dio/dio.dart';

void main() => runApp(MaterialApp(home: RDMultiHome(), theme: ThemeData.dark()));

class RDMultiHome extends StatefulWidget {
  @override
  _RDMultiHomeState createState() => _RDMultiHomeState();
}

class _RDMultiHomeState extends State<RDMultiHome> {
  final TextEditingController _controller = TextEditingController();
  final Dio _dio = Dio(BaseOptions(baseUrl: "/api")); // Netlify Proxy
  
  List<dynamic> _responses = [];
  bool _isLoading = false;
  
  // Available Free Models
  final List<String> _allModels = [
    "llama3-70b-8192", 
    "gemini-1.5-flash", 
    "command-r-plus"
  ];
  List<String> _selectedModels = ["llama3-70b-8192"];

  void _sendPrompt() async {
    if (_controller.text.isEmpty) return;
    setState(() { _isLoading = true; _responses = []; });

    try {
      final res = await _dio.post('/chat', data: {
        "prompt": _controller.text,
        "models": _selectedModels
      });
      setState(() { _responses = res.data['results']; });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error connecting to API")));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("RDmulti AI Aggregator")),
      body: Column(
        children: [
          // Model Selection
          Wrap(
            children: _allModels.map((m) => FilterChip(
              label: Text(m),
              selected: _selectedModels.contains(m),
              onSelected: (val) {
                setState(() => val ? _selectedModels.add(m) : _selectedModels.remove(m));
              },
            )).toList(),
          ),
          
          // Chat Results
          Expanded(
            child: _isLoading 
              ? Center(child: CircularProgressIndicator())
              : ListView.builder(
                  itemCount: _responses.length,
                  itemBuilder: (context, i) => Card(
                    color: Colors.grey[900],
                    margin: EdgeInsets.all(10),
                    child: Padding(
                      padding: EdgeInsets.all(15),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(_responses[i]['model'], style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue)),
                              Text("${_responses[i]['latency']}s", style: TextStyle(color: Colors.green)),
                            ],
                          ),
                          Divider(),
                          Text(_responses[i]['response']),
                        ],
                      ),
                    ),
                  ),
                ),
          ),
          
          // Input Field
          Padding(
            padding: EdgeInsets.all(10),
            child: Row(
              children: [
                Expanded(child: TextField(controller: _controller, decoration: InputDecoration(hintText: "Enter prompt..."))),
                IconButton(icon: Icon(Icons.send), onPressed: _sendPrompt),
              ],
            ),
          )
        ],
      ),
    );
  }
}