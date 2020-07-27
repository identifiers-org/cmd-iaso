use serde::de::{Deserialize, Deserializer};
use serde::ser::{Serialize, Serializer};

use super::WordString;

impl Serialize for WordString {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        self.0.serialize(serializer)
    }
}

impl<'de> Deserialize<'de> for WordString {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        Vec::<String>::deserialize(deserializer).map(WordString)
    }
}
