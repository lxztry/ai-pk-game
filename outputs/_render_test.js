
const canvasW = 600, canvasH = 600;
const mapW = 25, mapH = 25;
const states = [ [{"turn": 17, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [16.12576452749533, 21.228205378569648], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 36, "position": [20.185352100465494, 18.309344515598234], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": [{"position": [16.12576452749533, 21.228205378569648], "intensity": 1.0}, {"position": [20.185352100465494, 18.309344515598234], "intensity": 1.0}]}, {"turn": 0, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 100, "position": [10.408598023131743, 19.624838671659997], "direction": [0.3581959660517318, 0.9336464266007055], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 100, "position": [19.902518604829083, 7.912711222507882], "direction": [-0.7509163544682252, -0.6603973263060282], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 1, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 100, "position": [10.408598023131743, 19.624838671659997], "direction": [0.7770300194342609, 0.6294635405629083], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 100, "position": [19.902518604829083, 7.912711222507882], "direction": [-0.9805113022396975, -0.19646268393822935], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 2, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 100, "position": [10.408598023131743, 19.624838671659997], "direction": [0.9876595066146402, 0.15661640716644473], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 100, "position": [19.902518604829083, 7.912711222507882], "direction": [-0.9473790384064545, 0.32011397593366897], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 3, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 100, "position": [10.408598023131743, 19.624838671659997], "direction": [0.9336464266007055, -0.3581959660517317], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 100, "position": [19.902518604829083, 7.912711222507882], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 4, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 100, "position": [10.408598023131743, 19.624838671659997], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 100, "position": [19.902518604829083, 7.912711222507882], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [{"kind": "normal", "position": [17.921326625910996, 10.165460285912555], "direction": [-0.6603973263060288, 0.7509163544682247], "owner": "\u9632\u5b88\u6d3e"}], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 5, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 100, "position": [10.408598023131743, 19.624838671659997], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 100, "position": [19.902518604829083, 9.912711222507882], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [{"kind": "normal", "position": [15.94013464699291, 12.41820934931723], "direction": [-0.6603973263060288, 0.7509163544682247], "owner": "\u9632\u5b88\u6d3e"}, {"kind": "shotgun", "position": [11.703721626630344, 17.142369164966954], "direction": [0.46254414410664335, -0.8865962523903723], "owner": "\u6fc0\u8fdb\u6d3e"}, {"kind": "shotgun", "position": [12.171095936707887, 17.44915461724407], "direction": [0.6294635405629085, -0.7770300194342608], "owner": "\u6fc0\u8fdb\u6d3e"}, {"kind": "shotgun", "position": [12.568205016854941, 17.842677727002684], "direction": [0.7712882120439993, -0.6364860516633265], "owner": "\u6fc0\u8fdb\u6d3e"}], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 6, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 100, "position": [10.408598023131743, 17.624838671659997], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 100, "position": [17.902518604829083, 9.912711222507882], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [{"kind": "shotgun", "position": [13.933593850284032, 15.27347056282814], "direction": [0.6294635405629085, -0.7770300194342608], "owner": "\u6fc0\u8fdb\u6d3e"}, {"kind": "shotgun", "position": [14.72781201057814, 16.06051678234537], "direction": [0.7712882120439993, -0.6364860516633265], "owner": "\u6fc0\u8fdb\u6d3e"}], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 7, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 100, "position": [10.408598023131743, 17.624838671659997], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 84, "position": [17.902518604829083, 11.912711222507882], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": [{"position": [17.902518604829083, 11.912711222507882], "intensity": 1.0}]}, {"turn": 8, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 100, "position": [12.408598023131743, 17.624838671659997], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 84, "position": [17.902518604829083, 13.912711222507882], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 9, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 75, "position": [14.408598023131743, 17.624838671659997], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 84, "position": [17.902518604829083, 13.912711222507882], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": [{"position": [14.408598023131743, 17.624838671659997], "intensity": 1.0}]}, {"turn": 10, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 75, "position": [13.910609564702353, 17.8688681763672], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 84, "position": [18.400507063258473, 15.668681717800679], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 11, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 75, "position": [13.282165385508337, 18.424189981312765], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 60, "position": [17.02895124245249, 15.113359912855115], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": [{"position": [17.02895124245249, 15.113359912855115], "intensity": 1.0}]}, {"turn": 12, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 75, "position": [14.155965365931078, 19.26931752965578], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 60, "position": [18.15515126202975, 16.2682323645121], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 13, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 75, "position": [14.920158147033158, 19.888143560907007], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 60, "position": [19.390958480927672, 17.649406333260874], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 14, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 75, "position": [16.641068692634857, 21.215262312579153], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 60, "position": [17.67004793532597, 16.32228758158873], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 15, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 75, "position": [15.267419210081146, 20.40735076904839], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 60, "position": [19.04369741787968, 17.130199125119493], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 16, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 75, "position": [16.12576452749533, 21.228205378569648], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 60, "position": [20.185352100465494, 18.309344515598234], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 18, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [16.872466969693818, 21.787349398777884], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 36, "position": [21.43864965826701, 19.750200495389997], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 19, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [18.48611058009071, 23.177475786040482], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 36, "position": [19.82500604787012, 18.3600741081274], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 20, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [17.021777992537338, 22.07145738721365], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 36, "position": [21.28933863542349, 19.466092506954233], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 21, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [17.74015193444743, 22.413609826499876], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 36, "position": [22.5709646935134, 21.123940067668006], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 22, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [18.80165934944068, 23.870430864168902], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 36, "position": [21.50945727852015, 19.66711902999898], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 23, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [18.216404485770855, 24], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 12, "position": [22.094712142189973, 21.19090219222054], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": [{"position": [22.094712142189973, 21.19090219222054], "intensity": 1.0}]}, {"turn": 24, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [20.216404485770855, 24], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 12, "position": [22.094712142189973, 19.19090219222054], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 25, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [20.216404485770855, 22.0], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 12, "position": [22.094712142189973, 17.19090219222054], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 26, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [20.216404485770855, 20.0], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 12, "position": [22.094712142189973, 15.190902192220541], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 27, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [20.216404485770855, 18.0], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 12, "position": [22.094712142189973, 13.190902192220541], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 28, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [20.216404485770855, 16.0], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 0}, {"name": "\u9632\u5b88\u6d3e", "health": 12, "position": [22.094712142189973, 11.190902192220541], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": []}, {"turn": 29, "agents": [{"name": "\u6fc0\u8fdb\u6d3e", "health": 50, "position": [20.216404485770855, 16.0], "direction": [0.6294635405629085, -0.7770300194342608], "kills": 1}, {"name": "\u9632\u5b88\u6d3e", "health": -4, "position": [22.094712142189973, 9.190902192220541], "direction": [-0.6603973263060288, 0.7509163544682247], "kills": 0}], "bullets": [{"kind": "shotgun", "position": [22.376011479494053, 14.217839055342687], "direction": [0.7712882120439993, -0.6364860516633265], "owner": "\u6fc0\u8fdb\u6d3e"}], "obstacles": [{"rect": [12, 10, 2, 5]}, {"rect": [5, 18, 3, 3]}], "supplies": [{"position": [20, 12], "type": "health"}, {"position": [4, 4], "type": "ammo_shotgun"}], "explosions": [{"position": [22.094712142189973, 9.190902192220541], "intensity": 1.0}]}];];
const commentary = [{"turn": 0, "text": "\u2694\ufe0f  \u6fc0\u8fdb\u6d3e \u5bf9\u51b3 \u9632\u5b88\u6d3e\uff0c\u8c01\u662f\u6700\u7ec8\u80dc\u8005\uff1f", "importance": 3}, {"turn": 7, "text": "\ud83d\udca5 \u5f00\u5c40\u9996\u6740\uff01\u6fc0\u8fdb\u6d3e \u7ed9 \u9632\u5b88\u6d3e \u6765\u4e86\u4e00\u53d1\uff01", "importance": 3}, {"turn": 9, "text": "\ud83d\udd25 \u9006\u8f6c\uff01\u9632\u5b88\u6d3e \u6b8b\u8840\u53cd\u6740\uff01", "importance": 3}, {"turn": 11, "text": "\u26a1 \u6fc0\u8fdb\u6d3e \u4e0d\u5230\u6700\u540e\u4e00\u523b\u4e0d\u653e\u5f03\uff01", "importance": 3}, {"turn": 14, "text": "\ud83d\udca8 \u6fc0\u8fdb\u6d3e \u5b8c\u7f8e\u95ea\u907f\uff01\u5b50\u5f39\u64e6\u80a9\u800c\u8fc7\uff01", "importance": 2}, {"turn": 14, "text": "\ud83d\udc7b \u9632\u5b88\u6d3e \u7075\u6d3b\u5982\u9b3c\uff0c\u654c\u4eba\u7784\u4e0d\u51c6\uff01", "importance": 2}, {"turn": 19, "text": "\ud83d\udc7b \u6fc0\u8fdb\u6d3e \u7075\u6d3b\u5982\u9b3c\uff0c\u654c\u4eba\u7784\u4e0d\u51c6\uff01", "importance": 2}, {"turn": 19, "text": "\ud83d\udc7b \u9632\u5b88\u6d3e \u7075\u6d3b\u5982\u9b3c\uff0c\u654c\u4eba\u7784\u4e0d\u51c6\uff01", "importance": 2}, {"turn": 23, "text": "\ud83e\ude78 \u9632\u5b88\u6d3e \u8840\u7ebf\u544a\u6025 (12%)\uff0c\u9700\u8981\u8865\u7ed9\uff01", "importance": 2}, {"turn": 29, "text": "\u26a1 \u7ec8\u7ed3\u6280\uff01\u6fc0\u8fdb\u6d3e \u62ff\u4e0b \u9632\u5b88\u6d3e\uff01", "importance": 3}, {"turn": 29, "text": "\ud83c\udfc6 \u6bd4\u8d5b\u7ed3\u675f\uff01\u6fc0\u8fdb\u6d3e \u51fb\u8d25 \u9632\u5b88\u6d3e\uff01", "importance": 3}];];
const agentColors = {};
const stage = { innerHTML: '' };
const info = { innerHTML: '' };
const timeline = { value: 0, max: 10, oninput: null };
const frameLabel = { textContent: '' };
const frameTotal = { textContent: '17' };
const speedDisplay = { textContent: '6' };
let isPlaying = false, currentFrame = 0, lastTime = 0, fps = 6;
const agentColorList = ['#a855f7','#ec4899'];
states.forEach(f => { f.agents.forEach((a, i) => { if (!agentColors[a.name]) agentColors[a.name] = agentColorList[Object.keys(agentColors).length % agentColorList.length]; }); });

  if (frameIdx >= states.length) return;
  const f = states[frameIdx];
  const currentFrame = frameIdx;  // 给角色动画用
  // 统一缩放（地图不形变）+ 居中留白
  const scale = Math.min(canvasW / mapW, canvasH / mapH);
  const contentW = mapW * scale;
  const contentH = mapH * scale;
  const offsetX = (canvasW - contentW) / 2;
  const offsetY = (canvasH - contentH) / 2;
  const scaleX = scale, scaleY = scale;

  let svg = `<svg width="${canvasW}" height="${canvasH}" viewBox="0 0 ${canvasW} ${canvasH}" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<rect width="${canvasW}" height="${canvasH}" fill="#1e293b"/>`;
  svg += `<rect width="${canvasW}" height="${canvasH}" fill="#334155" opacity="0.3"/>`;

  // 网格（用统一 scale 避免形变）
  for (let x = 0; x <= mapW; x += 10) {
    const px = offsetX + x*scale;
    svg += `<line x1="${px}" y1="${offsetY}" x2="${px}" y2="${offsetY+contentH}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>`;
  }
  for (let y = 0; y <= mapH; y += 10) {
    const py = offsetY + y*scale;
    svg += `<line x1="${offsetX}" y1="${py}" x2="${offsetX+contentW}" y2="${py}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>`;
  }

  // 障碍物
  (f.obstacles || []).forEach(obs => {
    const [rx, ry, rw, rh] = obs.rect;
    const x = offsetX + rx * scaleX, y = offsetY + ry * scaleY, w = rw * scaleX, h = rh * scaleY;
    svg += `<g transform="translate(${x},${y})">`;
    svg += `<svg width="${w}" height="${h}" viewBox="0 0 32 32">`;
    svg += `<use href="#obstacle_brick" width="32" height="32"/>`;  // 关键：width/height
    svg += `</svg></g>`;
  });

  // 补给
  (f.supplies || []).forEach(s => {
    const sx = offsetX + s.position[0] * scaleX - 8;
    const sy = offsetY + s.position[1] * scaleY - 8;
    let kind = s.type;
    let svgId = 'supply_health';
    if (kind.includes('weapon_shotgun')) svgId = 'supply_weapon_sg';
    else if (kind.includes('weapon_sniper')) svgId = 'supply_weapon_sr';
    else if (kind.includes('weapon_rocket')) svgId = 'supply_weapon_rl';
    else if (kind.startsWith('ammo')) svgId = 'supply_ammo';
    // 关键：必须加 width/height，否则浏览器拉伸填满父容器
    svg += `<use href="#${svgId}" x="${sx-2}" y="${sy-2}" width="20" height="20"/>`;
  });

  // 子弹
  (f.bullets || []).forEach(b => {
    const bx = offsetX + b.position[0] * scaleX;
    const by = offsetY + b.position[1] * scaleY;
    const [dx, dy] = b.direction || [1, 0];
    const tx = bx - dx * 8, ty = by - dy * 8;
    // 尾迹
    svg += `<line x1="${tx}" y1="${ty}" x2="${bx}" y2="${by}" stroke="rgba(255,255,255,0.5)" stroke-width="1.5"/>`;
    // 关键：必须加 width/height
    svg += `<use href="#bullet_${b.kind || 'normal'}" x="${bx-5}" y="${by-5}" width="10" height="10"/>`;
  });

  // 爆炸 / 受击效果（缩小到合理范围）
  (f.explosions || []).forEach(e => {
    const ex = offsetX + e.position[0] * scaleX;
    const ey = offsetY + e.position[1] * scaleY;
    const r = 10;
    svg += `<circle cx="${ex}" cy="${ey}" r="${r}" fill="#fbbf24" opacity="0.7"/>`;
    svg += `<circle cx="${ex}" cy="${ey}" r="${r*0.6}" fill="#f97316" opacity="0.9"/>`;
    svg += `<circle cx="${ex}" cy="${ey}" r="${r*0.3}" fill="#fef3c7"/>`;
    // 放射线
    for (let i = 0; i < 6; i++) {
      const a = (Math.PI * 2 * i) / 6;
      const x1 = ex + Math.cos(a) * r * 0.5;
      const y1 = ey + Math.sin(a) * r * 0.5;
      const x2 = ex + Math.cos(a) * r * 1.3;
      const y2 = ey + Math.sin(a) * r * 1.3;
      svg += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round"/>`;
    }
    // 受击感叹号（8px）
    svg += `<text x="${ex}" y="${ey+3}" font-size="9" text-anchor="middle" fill="#000" font-weight="bold">!</text>`;
  });

  // Agent
  f.agents.forEach(a => {
    const ax = offsetX + a.position[0] * scaleX;
    const ay = offsetY + a.position[1] * scaleY;
    const [dx, dy] = a.direction || [1, 0];
    const deg = Math.atan2(dy, dx) * 180 / Math.PI;
    const color = agentColors[a.name] || '#3b82f6';
    const weapon = a.weapon || 'normal';
    const hp = Math.max(0, a.health) / 100;
    const face = hp > 0.5 ? 'happy' : (hp > 0.25 ? 'angry' : 'scared');
    const cx = 18, cy = 18, r = 12;
    const pupilOff = (deg > 90 || deg < -90) ? -2 : 2;
    const hpColor = hp > 0.5 ? '#22c55e' : (hp > 0.25 ? '#eab308' : '#ef4444');
    const weaponColor = {normal:'#888',shotgun:'#f97316',sniper:'#a855f7',rocket:'#dc2626'}[weapon];

    svg += `<g transform="translate(${ax-12},${ay-12})">`;
    svg += `<ellipse cx="12" cy="22" ry="2" rx="8" fill="rgba(0,0,0,0.4)"/>`;

    // 死亡：渲染骷髅
    if (a.health <= 0) {
      svg += `<circle cx="12" cy="11" r="8" fill="#fff" stroke="#000" stroke-width="2"/>`;
      svg += `<path d="M 5 8 Q 12 4 19 8" stroke="#000" stroke-width="1" fill="none"/>`;
      svg += `<circle cx="9" cy="10" r="3" fill="#000"/>`;
      svg += `<circle cx="15" cy="10" r="3" fill="#000"/>`;
      svg += `<polygon points="12,11 10,14 14,14" fill="#000"/>`;
      svg += `<line x1="8.5" y1="15" x2="8.5" y2="19" stroke="#000" stroke-width="1"/>`;
      svg += `<line x1="11" y1="15" x2="11" y2="19" stroke="#000" stroke-width="1"/>`;
      svg += `<line x1="13" y1="15" x2="13" y2="19" stroke="#000" stroke-width="1"/>`;
      svg += `<line x1="15.5" y1="15" x2="15.5" y2="19" stroke="#000" stroke-width="1"/>`;
      svg += `<text x="12" y="9" font-size="8" text-anchor="middle" fill="#dc2626" font-weight="bold">✕</text>`;
      svg += `</g>`;
      return;
    }

    // 走动动画：交替脚位置
    const walking = Math.abs(dx) + Math.abs(dy) > 0.01;
    const legPhase = walking ? Math.floor(currentFrame / 4) % 2 : 0;
    const legY = legPhase ? 21 : 22;
    const legOff = legPhase ? 0.8 : -0.8;
    svg += `<ellipse cx="${9+legOff}" cy="${legY}" rx="2" ry="1.2" fill="#333"/>`;
    svg += `<ellipse cx="${15-legOff}" cy="${legY}" rx="2" ry="1.2" fill="#333"/>`;

    svg += `<circle cx="12" cy="12" r="8" fill="${color}" stroke="#000" stroke-width="1.5"/>`;
    svg += `<circle cx="9" cy="9" r="2.5" fill="rgba(255,255,255,0.4)"/>`;
    // 表情：scared / angry / happy 三种
    if (face === 'scared') {
      // X 眼
      svg += `<line x1="7" y1="8" x2="11" y2="12" stroke="#000" stroke-width="1"/>`;
      svg += `<line x1="11" y1="8" x2="7" y2="12" stroke="#000" stroke-width="1"/>`;
      svg += `<line x1="13" y1="8" x2="17" y2="12" stroke="#000" stroke-width="1"/>`;
      svg += `<line x1="17" y1="8" x2="13" y2="12" stroke="#000" stroke-width="1"/>`;
      // O 嘴
      svg += `<ellipse cx="12" cy="16" rx="2" ry="2.5" fill="#000"/>`;
    } else if (face === 'angry') {
      // V 眉
      svg += `<line x1="6" y1="9" x2="10" y2="11" stroke="#000" stroke-width="1.2"/>`;
      svg += `<line x1="18" y1="9" x2="14" y2="11" stroke="#000" stroke-width="1.2"/>`;
      svg += `<circle cx="9" cy="10" r="1.2" fill="#000"/>`;
      svg += `<circle cx="15" cy="10" r="1.2" fill="#000"/>`;
      // 直线嘴
      svg += `<line x1="9" y1="16" x2="15" y2="16" stroke="#000" stroke-width="1.2"/>`;
    } else {
      // happy
      svg += `<circle cx="9" cy="10" r="1.5" fill="#fff"/>`;
      svg += `<circle cx="15" cy="10" r="1.5" fill="#fff"/>`;
      svg += `<circle cx="${9+pupilOff}" cy="10" r="0.8" fill="#000"/>`;
      svg += `<circle cx="${15+pupilOff}" cy="10" r="0.8" fill="#000"/>`;
      // 微笑
      svg += `<path d="M 9 15 Q 12 17 15 15" stroke="#000" stroke-width="1" fill="none"/>`;
    }
    // 武器（朝朝向）
    svg += `<g transform="rotate(${deg} 12 12)"><rect x="18" y="10.5" width="4" height="3" fill="${weaponColor}" stroke="#000" stroke-width="0.4"/></g>`;
    // 血量环
    const circ = 2 * Math.PI * 11;
    svg += `<circle cx="12" cy="12" r="11" fill="none" stroke="#333" stroke-width="1.5"/>`;
    svg += `<circle cx="12" cy="12" r="11" fill="none" stroke="${hpColor}" stroke-width="1.5" stroke-dasharray="${circ}" stroke-dashoffset="${circ*(1-hp)}" transform="rotate(-90 12 12)"/>`;
    svg += `</g>`;
  });

  svg += `</svg>`;
  stage.innerHTML = svg;

  // 信息面板
  let infoHtml = '';
  f.agents.forEach(a => {
    const color = agentColors[a.name] || '#3b82f6';
    const hp = Math.max(0, a.health);
    infoHtml += `<div class="card" style="border-left:4px solid ${color}">
      <b>${a.name}</b> · 血 ${hp}/100 · 击杀 ${a.kills || 0}
      <div class="hp"><div class="hpfill" style="width:${hp}%"></div></div>
      ${a.weapon && a.weapon !== 'normal' ? '<small>武器:' + a.weapon + '</small>' : ''}
    </div>`;
  });
  info.innerHTML = infoHtml;

  // 实时解说气泡（最近 1 个 importance>=3 事件）
  const recentComm = commentary.filter(c => c.turn <= frameIdx && c.turn > frameIdx - 5);
  // 找最近一个 importance>=3 的事件作为"飞过"气泡（最近 5 帧内）
  const flyIn = recentComm.filter(c => c.importance >= 3).pop();
  if (flyIn) {
    svg += `<g class="commentary-bubble" transform="translate(${canvasW/2 - 200}, 20)">
      <rect x="0" y="0" width="400" height="48" rx="10" fill="#fbbf24" stroke="#000" stroke-width="2" opacity="0.95"/>
      <text x="20" y="32" font-size="20" font-weight="bold" fill="#000" font-family="Microsoft YaHei, sans-serif">${flyIn.text.replace(/[<>&]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]))}</text>
    </g>`;
  }

  // 解说面板：画布下方显示最近 3 条
  let panelHtml = '<div class="comm-panel">';
  panelHtml += '<div class="comm-title">📺 实时解说</div>';
  // 取最近的 3 条（按 turn 升序）
  const displayComm = commentary.filter(c => c.turn <= frameIdx).slice(-3);
  if (displayComm.length === 0) {
    panelHtml += '<div class="comm-empty">（等待精彩时刻...）</div>';
  } else {
    displayComm.forEach(c => {
      const color = c.importance >= 3 ? '#fbbf24' : (c.importance >= 2 ? '#94a3b8' : '#475569');
      panelHtml += `<div class="comm-line" style="border-left:3px solid ${color}">
        <span class="comm-turn">[回合 ${c.turn}]</span>
        <span class="comm-text">${c.text}</span>
      </div>`;
    });
  }
  panelHtml += '</div>';
  // 用 innerHTML 设置（panel 在 stage 外的 div）
  const commPanel = document.getElementById('commentary');
  if (commPanel) commPanel.innerHTML = panelHtml;

  timeline.value = frameIdx;
  frameLabel.textContent = frameIdx;
// 模拟 frame 0
let svg = '';
renderFrame(0);
console.log('stage.innerHTML length:', stage.innerHTML.length);
console.log('contains bubble:', stage.innerHTML.includes('commentary-bubble'));
console.log('contains flyIn text:', stage.innerHTML.includes('激进派'));
// 打印最后 500 字
console.log('
--- last 500 chars ---');
console.log(stage.innerHTML.slice(-500));
