use serde::de::{Deserialize, Deserializer};
use serde::ser::{Serialize, Serializer};

use super::FrozenVecSet;

impl<T: Ord + PartialEq + Serialize> Serialize for FrozenVecSet<T> {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        self.0.serialize(serializer)
    }
}

impl<'de, T: Ord + PartialEq + Deserialize<'de>> Deserialize<'de> for FrozenVecSet<T> {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        Box::<[T]>::deserialize(deserializer).map(FrozenVecSet)
    }
}
