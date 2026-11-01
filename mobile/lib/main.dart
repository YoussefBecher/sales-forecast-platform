import 'package:dio/dio.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

// Chrome / Windows : 127.0.0.1 | Émulateur Android : http://10.0.2.2:8000
const baseUrl = 'http://127.0.0.1:8000';
final dio = Dio(
  BaseOptions(baseUrl: baseUrl, connectTimeout: const Duration(seconds: 10)),
);

void main() => runApp(const App());

class App extends StatelessWidget {
  const App({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    title: 'Prévision des ventes',
    theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
    home: const Home(),
  );
}

class Home extends StatefulWidget {
  const Home({super.key});
  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  int tab = 0;
  static const pages = [KpiPage(), ForecastPage(), AlertsPage()];

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Prévision des ventes')),
    body: pages[tab],
    bottomNavigationBar: NavigationBar(
      selectedIndex: tab,
      onDestinationSelected: (i) => setState(() => tab = i),
      destinations: const [
        NavigationDestination(icon: Icon(Icons.dashboard), label: 'KPI'),
        NavigationDestination(
          icon: Icon(Icons.show_chart),
          label: 'Prévisions',
        ),
        NavigationDestination(
          icon: Icon(Icons.warning_amber),
          label: 'Alertes',
        ),
      ],
    ),
  );
}

/// Charge des données de l'API et gère chargement / erreur.
class ApiView<T> extends StatefulWidget {
  final Future<T> Function() load;
  final Widget Function(BuildContext, T) builder;
  const ApiView({super.key, required this.load, required this.builder});
  @override
  State<ApiView<T>> createState() => _ApiViewState<T>();
}

class _ApiViewState<T> extends State<ApiView<T>> {
  late final Future<T> f = widget.load();
  @override
  Widget build(BuildContext context) => FutureBuilder<T>(
    future: f,
    builder: (c, s) {
      if (s.connectionState != ConnectionState.done) {
        return const Center(child: CircularProgressIndicator());
      }
      if (s.hasError) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Text('Erreur API : ${s.error}'),
          ),
        );
      }
      return widget.builder(c, s.data as T);
    },
  );
}

Widget tile(String label, String value, {Color? color}) => Card(
  child: ListTile(
    title: Text(label),
    trailing: Text(
      value,
      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color),
    ),
  ),
);

class KpiPage extends StatelessWidget {
  const KpiPage({super.key});
  @override
  Widget build(BuildContext context) => ApiView<Map>(
    load: () async => (await dio.get('/kpis')).data as Map,
    builder: (c, k) {
      final v = (k['variation_pct'] as num).toDouble();
      return ListView(
        padding: const EdgeInsets.all(16),
        children: [
          tile('CA des 30 derniers jours', '${(k['ca_30j'] as num).round()}'),
          tile(
            'Variation vs 30 jours précédents',
            '${v.toStringAsFixed(1)} %',
            color: v < 0 ? Colors.red : Colors.green,
          ),
          tile('Top catégorie', '${k['top_categorie']}'),
          tile('Top région', '${k['top_region']}'),
        ],
      );
    },
  );
}

class ForecastPage extends StatefulWidget {
  const ForecastPage({super.key});
  @override
  State<ForecastPage> createState() => _ForecastPageState();
}

class _ForecastPageState extends State<ForecastPage> {
  static const regions = ['Tunis', 'Sfax', 'Sousse', 'Nabeul'];
  static const categories = [
    'Électronique',
    'Mobilier',
    'Vêtements',
    'Alimentaire',
  ];
  String region = 'Tunis', category = 'Mobilier';

  Future<List> load() async =>
      (await dio.get(
            '/forecast',
            queryParameters: {
              'region': region,
              'category': category,
              'days': 7,
            },
          )).data
          as List;

  Widget dropdown(
    List<String> items,
    String value,
    void Function(String) onChanged,
  ) => Expanded(
    child: DropdownButton<String>(
      isExpanded: true,
      value: value,
      items: items
          .map((e) => DropdownMenuItem(value: e, child: Text(e)))
          .toList(),
      onChanged: (v) => setState(() => onChanged(v!)),
    ),
  );

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            dropdown(regions, region, (v) => region = v),
            const SizedBox(width: 12),
            dropdown(categories, category, (v) => category = v),
          ],
        ),
      ),
      Expanded(
        child: ApiView<List>(
          key: ValueKey('$region-$category'),
          load: load,
          builder: (c, data) {
            final spots = [
              for (var i = 0; i < data.length; i++)
                FlSpot(i.toDouble(), (data[i]['forecast'] as num).toDouble()),
            ];

            // Bornes de l'axe vertical avec une petite marge
            final ys = spots.map((s) => s.y);
            final lo = ys.reduce((a, b) => a < b ? a : b);
            final hi = ys.reduce((a, b) => a > b ? a : b);
            final pad = ((hi - lo) * 0.2).clamp(1.0, double.infinity);
            // Graduations rondes, adaptées à l'échelle
            final unit = hi > 500 ? 50.0 : 10.0;
            final minY = ((lo - pad) / unit).floor() * unit;
            final step = (((hi + pad - minY) / 4) / unit).ceil() * unit;
            final maxY = minY + step * 4;

            return Padding(
              padding: const EdgeInsets.fromLTRB(8, 16, 32, 8),
              child: LineChart(
                LineChartData(
                  minY: minY,
                  maxY: maxY,
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 52,
                        interval: step,
                        getTitlesWidget: (v, m) => Text(
                          v.round().toString(),
                          style: const TextStyle(fontSize: 11),
                        ),
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        interval: 1,
                        getTitlesWidget: (v, m) {
                          final i = v.toInt();
                          if (i < 0 || i >= data.length) {
                            return const SizedBox();
                          }
                          return Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(
                              (data[i]['date'] as String).substring(5),
                              style: const TextStyle(fontSize: 11),
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: false,
                      barWidth: 3,
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    ],
  );
}

class AlertsPage extends StatelessWidget {
  const AlertsPage({super.key});
  @override
  Widget build(BuildContext context) => ApiView<List>(
    load: () async => (await dio.get('/alerts')).data as List,
    builder: (c, a) => a.isEmpty
        ? const Center(child: Text('Aucune baisse détectée'))
        : ListView(
            children: [
              for (final x in a)
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.warning_amber, color: Colors.red),
                    title: Text('${x['region']} – ${x['category']}'),
                    subtitle: Text(
                      '${x['debut']} → ${x['fin']} (${x['jours']} j)',
                    ),
                    trailing: Text('ratio ${x['ratio_min']}'),
                  ),
                ),
            ],
          ),
  );
}
