import 'package:flutter/material.dart';

void main() => runApp(const ChillProsApp());

class Asset {
  Asset(this.id, this.type, this.customer, this.location, this.manufacturer,
      this.model, this.serial, this.refrigerant, this.health);
  final String id, type, customer, location, manufacturer, model, serial, refrigerant;
  final int health;
}

final demoAssets = <Asset>[
  Asset('CP-SA-000014','RTU','Broadway Bistro','Roof • Zone 2','Trane','YSC060E3','2419K4R7H','R-410A',84),
  Asset('CP-SA-000006','Ice Machine','Riverwalk Hotel','Main kitchen','Manitowoc','IDT0750A','110728392','R-410A',97),
  Asset('CP-SA-000003','Walk-In Cooler','Alamo Market','Receiving area','Heatcraft','BZT060','HTC992801','R-404A',72),
  Asset('CP-SA-000021','Reach-In','Southtown Cafe','Prep line','True','T-49-HC','10877654','R-290',93),
];

class ChillProsApp extends StatelessWidget {
  const ChillProsApp({super.key});
  @override Widget build(BuildContext context) {
    const ice = Color(0xFF27B7F5);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Chill Pros AMS',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: ice, brightness: Brightness.light),
        scaffoldBackgroundColor: const Color(0xFFF3F7FA),
        useMaterial3: true,
        cardTheme: const CardThemeData(margin: EdgeInsets.zero),
      ),
      home: const Shell(),
    );
  }
}

class Shell extends StatefulWidget {
  const Shell({super.key});
  @override State<Shell> createState() => _ShellState();
}

class _ShellState extends State<Shell> {
  int index = 0;
  final pages = const [DashboardPage(), AssetsPage(), AddAssetPage(), ScannerPage()];
  @override Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('CHILL PROS', style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1)),
          Text('OPERATIONS OVERLAY', style: TextStyle(fontSize: 10, letterSpacing: 1.5)),
        ]),
        actions: const [Padding(padding: EdgeInsets.only(right: 16), child: Chip(label: Text('Owner')))],
      ),
      body: pages[index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (value) => setState(() => index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.ac_unit_outlined), label: 'Assets'),
          NavigationDestination(icon: Icon(Icons.add_circle_outline), label: 'Add'),
          NavigationDestination(icon: Icon(Icons.qr_code_scanner), label: 'Scan'),
        ],
      ),
    );
  }
}

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key});
  @override Widget build(BuildContext context) {
    return ListView(padding: const EdgeInsets.all(16), children: [
      Container(
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [Color(0xFF071A2B), Color(0xFF123D55)]),
          borderRadius: BorderRadius.circular(20),
        ),
        child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('LIVE OPERATIONS', style: TextStyle(color: Color(0xFF67D5FF), fontSize: 11, letterSpacing: 2)),
          SizedBox(height: 8),
          Text('Good afternoon, Chill Pros', style: TextStyle(color: Colors.white, fontSize: 25, fontWeight: FontWeight.w800)),
          SizedBox(height: 6),
          Text('Manage assets, service activity, and PM compliance.', style: TextStyle(color: Color(0xFFC4DAE6))),
        ]),
      ),
      const SizedBox(height: 16),
      GridView.count(
        crossAxisCount: MediaQuery.sizeOf(context).width > 700 ? 4 : 2,
        shrinkWrap: true, physics: const NeverScrollableScrollPhysics(),
        crossAxisSpacing: 12, mainAxisSpacing: 12, childAspectRatio: 1.45,
        children: const [
          MetricCard('Assets Managed','248','17 locations'),
          MetricCard('Open Work Orders','14','4 approvals'),
          MetricCard('PM Due','23','This week'),
          MetricCard('Asset Health','89%','Portfolio average'),
        ],
      ),
      const SizedBox(height: 16),
      Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Priority Assets', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          ...demoAssets.take(3).map((a) => ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const CircleAvatar(child: Icon(Icons.ac_unit)),
            title: Text('${a.id} • ${a.type}', style: const TextStyle(fontWeight: FontWeight.w800)),
            subtitle: Text('${a.customer} • ${a.location}'),
            trailing: HealthBadge(a.health),
          )),
        ],
      ))),
    ]);
  }
}

class MetricCard extends StatelessWidget {
  const MetricCard(this.label,this.value,this.note,{super.key});
  final String label,value,note;
  @override Widget build(BuildContext context) => Card(child: Padding(
    padding: const EdgeInsets.all(15),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [
      Text(label, style: const TextStyle(fontSize: 12, color: Colors.blueGrey)),
      Text(value, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w900)),
      Text(note, style: const TextStyle(fontSize: 11, color: Colors.blueGrey)),
    ]),
  ));
}

class SectionCard extends StatelessWidget {
  const SectionCard({required this.title, required this.child, super.key});
  final String title; final Widget child;
  @override Widget build(BuildContext context) => Card(child: Padding(
    padding: const EdgeInsets.all(16),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
      const SizedBox(height: 12), child
    ]),
  ));
}

class AssetsPage extends StatefulWidget {
  const AssetsPage({super.key});
  @override State<AssetsPage> createState()=>_AssetsPageState();
}
class _AssetsPageState extends State<AssetsPage> {
  String query='';
  @override Widget build(BuildContext context) {
    final filtered=demoAssets.where((a)=>'${a.id} ${a.type} ${a.customer} ${a.model}'.toLowerCase().contains(query.toLowerCase()));
    return ListView(padding: const EdgeInsets.all(16), children: [
      TextField(onChanged:(v)=>setState(()=>query=v), decoration: const InputDecoration(
        prefixIcon: Icon(Icons.search), hintText:'Search asset ID, customer, model or serial',
        filled:true, fillColor:Colors.white, border:OutlineInputBorder(borderSide:BorderSide.none))),
      const SizedBox(height:12),
      ...filtered.map((a)=>Card(margin: const EdgeInsets.only(bottom:10), child: ListTile(
        leading: const CircleAvatar(child:Icon(Icons.ac_unit)),
        title: Text('${a.id} • ${a.type}', style: const TextStyle(fontWeight: FontWeight.w800)),
        subtitle: Text('${a.customer}\n${a.location} • ${a.manufacturer} ${a.model}'),
        isThreeLine:true,
        trailing: HealthBadge(a.health),
        onTap:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>AssetDetailPage(asset:a))),
      )))
    ]);
  }
}

class HealthBadge extends StatelessWidget {
  const HealthBadge(this.health,{super.key}); final int health;
  @override Widget build(BuildContext context) {
    final color=health>=90?Colors.green:health>=75?Colors.orange:Colors.red;
    return Chip(label:Text('$health%',style:TextStyle(color:color,fontWeight:FontWeight.w900)),
      backgroundColor:color.withValues(alpha:.1), side:BorderSide.none);
  }
}

class AssetDetailPage extends StatelessWidget {
  const AssetDetailPage({required this.asset,super.key}); final Asset asset;
  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:Text(asset.id)),
    body:ListView(padding:const EdgeInsets.all(16),children:[
      Container(padding:const EdgeInsets.all(20),decoration:BoxDecoration(
        gradient:const LinearGradient(colors:[Color(0xFF071A2B),Color(0xFF123D55)]),
        borderRadius:BorderRadius.circular(18)),
        child:Row(children:[
          const CircleAvatar(radius:38,backgroundColor:Color(0x22FFFFFF),child:Icon(Icons.ac_unit,color:Colors.white,size:38)),
          const SizedBox(width:16),
          Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
            Text(asset.type,style:const TextStyle(color:Colors.white,fontSize:24,fontWeight:FontWeight.w900)),
            Text('${asset.customer} • ${asset.location}',style:const TextStyle(color:Color(0xFFC4DAE6))),
          ])),
          HealthBadge(asset.health),
        ])),
      const SizedBox(height:14),
      SectionCard(title:'Equipment Information',child:Column(children:[
        DataRowView('Manufacturer',asset.manufacturer),DataRowView('Model',asset.model),
        DataRowView('Serial',asset.serial),DataRowView('Refrigerant',asset.refrigerant),
      ])),
      const SizedBox(height:14),
      const SectionCard(title:'Service Timeline',child:Column(children:[
        ListTile(contentPadding:EdgeInsets.zero,leading:Icon(Icons.build_circle_outlined),title:Text('Preventive Maintenance'),subtitle:Text('Cooling inspection completed • 06/18/2026')),
        ListTile(contentPadding:EdgeInsets.zero,leading:Icon(Icons.history),title:Text('Corrective Repair'),subtitle:Text('Electrical component replaced • 03/02/2026')),
      ])),
    ]));
}

class DataRowView extends StatelessWidget {
  const DataRowView(this.label,this.value,{super.key}); final String label,value;
  @override Widget build(BuildContext context)=>Padding(padding:const EdgeInsets.symmetric(vertical:8),child:Row(
    children:[Expanded(child:Text(label,style:const TextStyle(color:Colors.blueGrey))),Expanded(child:Text(value,style:const TextStyle(fontWeight:FontWeight.w800)))]));
}

class AddAssetPage extends StatelessWidget {
  const AddAssetPage({super.key});
  @override Widget build(BuildContext context)=>ListView(padding:const EdgeInsets.all(16),children:[
    const Text('Add New Asset',style:TextStyle(fontSize:25,fontWeight:FontWeight.w900)),
    const Text('Create the standardized Chill Pros equipment record.',style:TextStyle(color:Colors.blueGrey)),
    const SizedBox(height:16),
    Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(children:[
      for(final label in ['Customer','Location','Equipment Type','Manufacturer','Model Number','Serial Number','Refrigerant'])
        Padding(padding:const EdgeInsets.only(bottom:12),child:TextField(decoration:InputDecoration(labelText:label,border:const OutlineInputBorder()))),
      SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:(){},icon:const Icon(Icons.qr_code),label:const Text('Create Asset & Generate ID')))
    ])))
  ]);
}

class ScannerPage extends StatelessWidget {
  const ScannerPage({super.key});
  @override Widget build(BuildContext context)=>Center(child:SingleChildScrollView(padding:const EdgeInsets.all(24),child:Column(children:[
    Container(width:230,height:230,decoration:BoxDecoration(border:Border.all(color:const Color(0xFF27B7F5),width:5),borderRadius:BorderRadius.circular(22)),
      child:const Icon(Icons.qr_code_scanner,size:100,color:Color(0xFF9FC9DB))),
    const SizedBox(height:20),
    const Text('Scan Chill Pros Asset Tag',style:TextStyle(fontSize:23,fontWeight:FontWeight.w900)),
    const SizedBox(height:8),
    const Text('Camera integration is reserved for the next build.',textAlign:TextAlign.center,style:TextStyle(color:Colors.blueGrey)),
    const SizedBox(height:16),
    FilledButton.icon(onPressed:(){},icon:const Icon(Icons.camera_alt),label:const Text('Start Scanner')),
  ])));
}
